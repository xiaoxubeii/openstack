## LibvirtDriver注册事件过程 ##
在nova/virt/libvirt/driver.py的\_get\_new\_connection()中有：

    wrapped_conn.domainEventRegisterAny(
                None,
                libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
                self._event_lifecycle_callback,
                self)
                
我们知道wrapped_conn其实是已建立的virConn的包装类，在https://wiki.openstack.org/wiki/ComputeDriverEvents 下可找到ComputeDriverEvents的事件设计原理。  

看Libvirt Design部分：

> Invoking conn.domainEventRegisterAny() will register event callbacks against libvirt connection instances. The callbacks registered will be triggered from the execution context of virEventRunDefaultImpl()

conn.domainEventRegisterAny()是通过libvirt的connection实例来注册事件的callback。注册的callback会在virEventRunDefaultImpl()期间被触发。  

看wrapped_conn.domaineventRegisterAny()的参数，libvirt.VIR\_DOMAIN\_EVENT\_ID\_LIFECYCLE是domain生命周期的事件，一旦domain有事件发生，那么就会回调self.\_event\_lifecycle\_callback。  

看_event_lifecycle_callback()：

    @staticmethod
    def _event_lifecycle_callback(conn, dom, event, detail, opaque):
        """Receives lifecycle events from libvirt.

        NB: this method is executing in a native thread, not
        an eventlet coroutine. It can oyum inly invoke other libvirt
        APIs, or use self.queue_event(). Any use of logging APIs
        in particular is forbidden.
        """

        self = opaque

        uuid = dom.UUIDString()
        transition = None
        if event == libvirt.VIR_DOMAIN_EVENT_STOPPED:
            transition = virtevent.EVENT_LIFECYCLE_STOPPED
        elif event == libvirt.VIR_DOMAIN_EVENT_STARTED:
            transition = virtevent.EVENT_LIFECYCLE_STARTED
        elif event == libvirt.VIR_DOMAIN_EVENT_SUSPENDED:
            transition = virtevent.EVENT_LIFECYCLE_PAUSED
        elif event == libvirt.VIR_DOMAIN_EVENT_RESUMED:
            transition = virtevent.EVENT_LIFECYCLE_RESUMED

        if transition is not None:
            self._queue_event(virtevent.LifecycleEvent(uuid, transition))
            
@staticmethod表明它是一个静态函数，并且，它只关注4类事件，分别是VIR\_DOMAIN\_EVENT\_STOPPED、VIR\_DOMAIN\_EVENT\_STARTED、VIR\_DOMAIN\_EVENT\_SUSPENDED、VIR\_DOMAIN\_EVENT\_RESUMED。这4类事件会被转换成相应的virtevent事件，最后创建LifecycleEvent，并发送到事件队列中。  

随后会有一个green thread从队列中取出事件并分发给self.\_compute\_event\_callback()，这个函数是由register\_event\_listener进行赋值：

    def register_event_listener(self, callback):
        """Register a callback to receive events.

        Register a callback to receive asynchronous event
        notifications from hypervisors. The callback will
        be invoked with a single parameter, which will be
        an instance of the nova.virt.event.Event class.
        """

        self._compute_event_callback = callback
        
系统会在nova/compute/manager.py的init_virt_events中赋值，实际是在handle\_events()中调用handle\_lifecycle\_event()进行事件处理：

    def handle_events(self, event):
        if isinstance(event, virtevent.LifecycleEvent):
            try:
                self.handle_lifecycle_event(event)
            except exception.InstanceNotFound:
                LOG.debug(_("Event %s arrived for non-existent instance. The "
                            "instance was probably deleted.") % event)
        else:
            LOG.debug(_("Ignoring event %s") % 
            
    def handle_lifecycle_event(self, event):
        LOG.info(_("Lifecycle event %(state)d on VM %(uuid)s") %
                  {'state': event.get_transition(),
                   'uuid': event.get_instance_uuid()})
        context = nova.context.get_admin_context()
        instance = instance_obj.Instance.get_by_uuid(
            context, event.get_instance_uuid())
        vm_power_state = None
        if event.get_transition() == virtevent.EVENT_LIFECYCLE_STOPPED:
            vm_power_state = power_state.SHUTDOWN
        elif event.get_transition() == virtevent.EVENT_LIFECYCLE_STARTED:
            vm_power_state = power_state.RUNNING
        elif event.get_transition() == virtevent.EVENT_LIFECYCLE_PAUSED:
            vm_power_state = power_state.PAUSED
        elif event.get_transition() == virtevent.EVENT_LIFECYCLE_RESUMED:
            vm_power_state = power_state.RUNNING
        else:
            LOG.warning(_("Unexpected power state %d") %
                        event.get_transition())

        if vm_power_state is not None:
            self._sync_instance_power_state(context,
                                            instance,
                                            vm_power_state)

那么，Libvirt事件是如何启动监听的呢？其实是在nova/virt/libvirt/driver.py中的init\_host()：

    def init_host(self, host):
        self._do_quality_warnings()
        libvirt.registerErrorHandler(libvirt_error_handler, None)
        libvirt.virEventRegisterDefaultImpl()

        if not self.has_min_version(MIN_LIBVIRT_VERSION):
            major = MIN_LIBVIRT_VERSION[0]
            minor = MIN_LIBVIRT_VERSION[1]
            micro = MIN_LIBVIRT_VERSION[2]
            LOG.error(_('Nova requires libvirt version '
                        '%(major)i.%(minor)i.%(micro)i or greater.'),
                      {'major': major, 'minor': minor, 'micro': micro})

        self._init_events()
        
libvirt.virEventRegisterDefaultImpl()会注册libvirt默认的事件callback，并且在最后\_init\_events()进行初始化：

    def _init_events(self):
        """Initializes the libvirt events subsystem.

        This requires running a native thread to provide the
        libvirt event loop integration. This forwards events
        to a green thread which does the actual dispatching.
        """

        self._init_events_pipe()//初始化事件队列

        LOG.debug(_("Starting native event thread"))
        event_thread = native_threading.Thread(target=self._native_thread)
        event_thread.setDaemon(True)
        event_thread.start()

        LOG.debug(_("Starting green dispatch thread"))
        eventlet.spawn(self._dispatch_thread)
        
event\_thread = native\_threading.Thread(target=self.\_native\_thread)会启动一个native thread用来进行事件的监听：

    def _native_thread(self):
        """Receives async events coming in from libvirtd.

        This is a native thread which runs the default
        libvirt event loop implementation. This processes
        any incoming async events from libvirtd and queues
        them for later dispatch. This thread is only
        permitted to use libvirt python APIs, and the
        driver.queue_event method. In particular any use
        of logging is forbidden, since it will confuse
        eventlet's greenthread integration
        """

        while True:
            libvirt.virEventRunDefaultImpl()
            
至此，LibvirtDriver的事件注册、监听过程就结束了。




