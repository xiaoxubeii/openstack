## LibvirtDriverע���¼����� ##
��nova/virt/libvirt/driver.py��_get_new_connection()���У�

    wrapped_conn.domainEventRegisterAny(
                None,
                libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
                self._event_lifecycle_callback,
                self)
                
����֪��wrapped_conn��ʵ���ѽ�����virConn�İ�װ�࣬��https://wiki.openstack.org/wiki/ComputeDriverEvents�¿��ҵ�ComputeDriverEvents���¼����ԭ��  

��Libvirt Design���֣�

> Invoking conn.domainEventRegisterAny() will register event callbacks against libvirt connection instances. The callbacks registered will be triggered from the execution context of virEventRunDefaultImpl()

conn.domainEventRegisterAny()��ͨ��libvirt��connectionʵ����ע���¼���callback��ע���callback����virEventRunDefaultImpl()�ڼ䱻������  

��wrapped_conn.domaineventRegisterAny()�Ĳ�����libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE��domain�������ڵ��¼���һ��domain���¼���������ô�ͻ�ص�self._event_lifecycle_callback��  

��_event_lifecycle_callback()��

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
            
@staticmethod��������һ����̬���������ң���ֻ��ע4���¼����ֱ���VIR_DOMAIN_EVENT_STOPPED��VIR_DOMAIN_EVENT_STARTED��VIR_DOMAIN_EVENT_SUSPENDED��VIR_DOMAIN_EVENT_RESUMED����4���¼��ᱻת������Ӧ��virtevent�¼�����󴴽�LifecycleEvent�������͵��¼������С�  

������һ��green thread�Ӷ�����ȡ���¼����ַ���self._compute_event_callback()�������������register_event_listener���и�ֵ��

    def register_event_listener(self, callback):
        """Register a callback to receive events.

        Register a callback to receive asynchronous event
        notifications from hypervisors. The callback will
        be invoked with a single parameter, which will be
        an instance of the nova.virt.event.Event class.
        """

        self._compute_event_callback = callback
        
ϵͳ����nova/compute/manager.py��init_virt_events�и�ֵ��ʵ������handle_events()�е���handle_lifecycle_event()�����¼�����

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

��ô��Libvirt�¼�����������������أ���ʵ����nova/virt/libvirt/driver.py�е�init_host()��

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
        
libvirt.virEventRegisterDefaultImpl()��ע��libvirtĬ�ϵ��¼�callback�����������_init_events()���г�ʼ����

    def _init_events(self):
        """Initializes the libvirt events subsystem.

        This requires running a native thread to provide the
        libvirt event loop integration. This forwards events
        to a green thread which does the actual dispatching.
        """

        self._init_events_pipe()//��ʼ���¼�����

        LOG.debug(_("Starting native event thread"))
        event_thread = native_threading.Thread(target=self._native_thread)
        event_thread.setDaemon(True)
        event_thread.start()

        LOG.debug(_("Starting green dispatch thread"))
        eventlet.spawn(self._dispatch_thread)
        
event_thread = native_threading.Thread(target=self._native_thread)������һ��native thread���������¼��ļ�����

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
            
���ˣ�LibvirtDriver���¼�ע�ᡢ�������̾ͽ����ˡ�




