## Conceptual architecture ##


----------


The architecture includes 4 parts, there are Controller, Compute, Network and Share Storage.

 1. Controller 
The Controller node runs the Identity Service, Image, Service, dashboard, Block Storage Service, Meter Service and management portion of Compute. It also contains the related API Services, MySQL databases and messaging system.

 2. Compute
The Compute node runs the hypervisor portion of Compute, which operates tenant virtual machines. By default, Compute uses KVM as the hypervisor. Compute also provisions and operates tenant networks and implements security groups.

 3. Network
The Network node runs the tenant network and the vm instance connectivity, with both other vms and external network. Network also provisions associated network services, such as NAT, Firewall, Load Balance, QoS and so on.

 4. Share Storage
The Share Storage runs the storage service for such as compute, block storage, image and which needs storage. It can provisions Object, File System and Block storage. In this architecture, it is the storage backend for compute Root and Ephemeral Storage, Volume Storage and OS Image Storage.

## Physical architecture ##


----------


## Service architecture ##


----------


