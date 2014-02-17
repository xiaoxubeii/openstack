## LibvirtDriver创建connection过程 ##

在nova.virt.libvirt.driver中，LibvirtDriver是Nova Compute的驱动，通过Libvirt管理虚拟机。
首先看连接过程：

    def _get_connection(self):
        # multiple concurrent connections are protected by _wrapped_conn_lock
        with self._wrapped_conn_lock://给thread加锁
            wrapped_conn = self._wrapped_conn
            if not wrapped_conn or not self._test_connection(wrapped_conn):
                wrapped_conn = self._get_new_connection()//获取新的connection

        return wrapped_conn
        
    _conn = property(_get_connection)//将_get_connection当做一个属性来使用
        
通过_get_new_connection()，获取新的connection：

    def _get_new_connection(self):
        # call with _wrapped_conn_lock held
        LOG.debug(_('Connecting to libvirt: %s'), self.uri())
        wrapped_conn = None

        try:
            wrapped_conn = self._connect(self.uri(), self.read_only)//获取只读connection
        finally:
            # Enabling the compute service, in case it was disabled
            # since the connection was successful.
            is_connected = bool(wrapped_conn)
            self.set_host_enabled(CONF.host, is_connected)

        self._wrapped_conn = wrapped_conn

        try:
            LOG.debug(_("Registering for lifecycle events %s"), self)
            wrapped_conn.domainEventRegisterAny(
                None,
                libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
                self._event_lifecycle_callback,
                self)//注册event，这个随后再讲
        except Exception as e:
            LOG.warn(_("URI %(uri)s does not support events: %(error)s"),
                     {'uri': self.uri(), 'error': e})

        ...

        return wrapped_conn
        
在self._connect()中获取connection：

    @staticmethod
    def _connect(uri, read_only):
        def _connect_auth_cb(creds, opaque):
            ...

        auth = [[libvirt.VIR_CRED_AUTHNAME,
                 libvirt.VIR_CRED_ECHOPROMPT,
                 libvirt.VIR_CRED_REALM,
                 libvirt.VIR_CRED_PASSPHRASE,
                 libvirt.VIR_CRED_NOECHOPROMPT,
                 libvirt.VIR_CRED_EXTERNAL],
                _connect_auth_cb,
                None]

        try:
            flags = 0
            if read_only:
                flags = libvirt.VIR_CONNECT_RO
            # tpool.proxy_call creates a native thread. Due to limitations
            # with eventlet locking we cannot use the logging API inside
            # the called function.
            //通过eventlet的tpool来获得一个naive thread
            return tpool.proxy_call(
                (libvirt.virDomain, libvirt.virConnect),
                libvirt.openAuth, uri, auth, flags)
        except libvirt.libvirtError as ex:
            LOG.exception(_("Connection to libvirt failed: %s"), ex)
            payload = dict(ip=LibvirtDriver.get_host_ip_addr(),
                           method='_connect',
                           reason=ex)
            rpc.get_notifier('compute').error(nova_context.get_admin_context(),
                                              'compute.libvirt.error',
                                              payload)
            raise exception.HypervisorUnavailable(host=CONF.host)
            
看tpool.proxy_call()，查eventlet的源码可知，这个函数是用来生成一个naive thread，并将返回值进行wrap。
在eventlet/eventlet/tpool.py里：

    def proxy_call(autowrap, f, *args, **kwargs):
    """
    Call a function *f* and returns the value.  If the type of the return value
    is in the *autowrap* collection, then it is wrapped in a :class:`Proxy`
    object before return.

    Normally *f* will be called in the threadpool with :func:`execute`; if the
    keyword argument "nonblocking" is set to ``True``, it will simply be
    executed directly.  This is useful if you have an object which has methods
    that don't need to be called in a separate thread, but which return objects
    that should be Proxy wrapped.
    """
    if kwargs.pop('nonblocking',False):
        rv = f(*args, **kwargs)
    else:
        rv = execute(f,*args,**kwargs)
    if isinstance(rv, autowrap):
        return Proxy(rv, autowrap)
    else:
        return rv
看注释可知，参数autowrap是要包装的值，f是执行的函数，*args是f的参数，**kwargs是keyword argument，比如"nonblocking"。
结合_connect()中的代码：

    @staticmethod
    def _connect(uri, read_only):
        ...
        return tpool.proxy_call((libvirt.virDomain, libvirt.virConnect), libvirt.openAuth, uri, auth, flags)
    
意思就是说，开启一个新的naive thread来执行libvirt.openAuth，并将返回的类型为(libvirt.virDomain, libvirt.virtConnect)的值包装起来。

然后通过_conn即可通过libvirt来管理虚拟机，比如：

    _conn.listDomainsID()//获取所有domain的id



