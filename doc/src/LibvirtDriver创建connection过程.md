## LibvirtDriver����connection���� ##

��nova.virt.libvirt.driver�У�LibvirtDriver��Nova Compute��������ͨ��Libvirt�����������
���ȿ����ӹ��̣�

    def _get_connection(self):
        # multiple concurrent connections are protected by _wrapped_conn_lock
        with self._wrapped_conn_lock://��thread����
            wrapped_conn = self._wrapped_conn
            if not wrapped_conn or not self._test_connection(wrapped_conn):
                wrapped_conn = self._get_new_connection()//��ȡ�µ�connection

        return wrapped_conn
        
    _conn = property(_get_connection)//��_get_connection����һ��������ʹ��
        
ͨ��_get_new_connection()����ȡ�µ�connection��

    def _get_new_connection(self):
        # call with _wrapped_conn_lock held
        LOG.debug(_('Connecting to libvirt: %s'), self.uri())
        wrapped_conn = None

        try:
            wrapped_conn = self._connect(self.uri(), self.read_only)//��ȡֻ��connection
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
                self)//ע��event���������ٽ�
        except Exception as e:
            LOG.warn(_("URI %(uri)s does not support events: %(error)s"),
                     {'uri': self.uri(), 'error': e})

        ...

        return wrapped_conn
        
��self._connect()�л�ȡconnection��

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
            //ͨ��eventlet��tpool�����һ��naive thread
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
            
��tpool.proxy_call()����eventlet��Դ���֪�������������������һ��naive thread����������ֵ����wrap��
��eventlet/eventlet/tpool.py�

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
��ע�Ϳ�֪������autowrap��Ҫ��װ��ֵ��f��ִ�еĺ�����*args��f�Ĳ�����**kwargs��keyword argument������"nonblocking"��
���_connect()�еĴ��룺

    @staticmethod
    def _connect(uri, read_only):
        ...
        return tpool.proxy_call((libvirt.virDomain, libvirt.virConnect), libvirt.openAuth, uri, auth, flags)
    
��˼����˵������һ���µ�naive thread��ִ��libvirt.openAuth���������ص�����Ϊ(libvirt.virDomain, libvirt.virtConnect)��ֵ��װ������

Ȼ��ͨ��_conn����ͨ��libvirt����������������磺

    _conn.listDomainsID()//��ȡ����domain��id



