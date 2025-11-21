# File that contains functions to manage hypervisor (checker https://libvirt.org/python.html)

import libvirt
import sys
from objects.DomainInfo import DomainInfo
from flask import make_response

# Take an ip of an hypervisor and return the connector to it
def get_connector_to_node(ip):
    try:
        conn = libvirt.open(f"qemu+ssh://{ip}/system")
        return conn
    except libvirt.libvirtError:
        print('Failed to open connection to the hypervisor')
        sys.exit(1)

def get_node_info(conn):
    nodeInfo = conn.getInfo()
    return nodeInfo

def get_domain_info(conn, id):
    dom = conn.lookupByID(id)
    info = libvirt.virDomainGetInfo(dom)

# Cette méthode renvoie une liste de DomainInfo, qui contienne leur propose objet Domain, ce qui permettra de l'utiliser pour certains actions 
# TODO: : On pourrait mettre les DomainInfo dans une bdd relationnelle
def get_all_domain_info(conn):
    domains = []
    domainsInfos = conn.getAllDomainStats()
    for domain in domainsInfos:
       domains.append(DomainInfo(domain[0], domain[1]))
    return domains

# Starting a existing domain
def create_domain(conn, name):
    try:
        dom = conn.lookupByName(name)
        dom.create()
        return make_response("Success", 200)
    except libvirt.libvirtError:
        print('libvirtError: Failed to create domain')
        return make_response("libvirtError: Error when creating domain", 400)
    except :
        print("Unknown error: Failed to create domain")
        return make_response("Unknown: Error when creating domain", 400)

# Shutdown a domain
def destroy_domain(conn, name):
    try:
        dom = conn.lookupByName(name)
        dom.destroy()
        return make_response("<h1>Success</h1>", 200)
    except libvirt.libvirtError:
        print('libvirtError: Failed to destroy domain')
        return make_response("<h1>libvirtError: Error when destroying domain</h1>", 400)
    except :
        print("Unknown error: Failed to destroy domain")
        return make_response("<h1>Unknown: Error when destroying domain</h1>", 400)

def undefine_domain(conn, name):
    # NOTE: VM need to be shutdown to see the effect !
    # Don't delete the VM disk - Error if found an external snapshot (libvirt can't delete it: https://wiki.libvirt.org/I_created_an_external_snapshot_but_libvirt_will_not_let_me_delete_or_revert_to_it.html)
    try:
        dom = conn.lookupByName(name)
        flags = libvirt.VIR_DOMAIN_UNDEFINE_NVRAM
        if dom.hasManagedSaveImage():
            flags ^= libvirt.VIR_DOMAIN_UNDEFINE_MANAGED_SAVE
        if dom.hasCurrentSnapshot():
            for snapshot in dom.listAllSnapshots():
                snapshot.delete()
            flags ^= libvirt.VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA
        if dom.listAllCheckpoints():
            flags ^= libvirt.VIR_DOMAIN_UNDEFINE_CHECKPOINTS_METADATA
        
        dom.undefineFlags(flags)
        destroy_domain(conn, name)
        return make_response("<h1>Success</h1>", 200)

    except libvirt.libvirtError:
        return make_response("<h1>libvirtError: Error when undefine domain</h1>", 400)
    except Exception as e:
        return make_response("<h1>Unknown: Error when undefine domain</h1>", 400)

def get_snapshot_name_domain(conn, name):
    """
        Return a list of all snapshot name attached to the domain name. The first snapshot name in the list is the current.
    """
    try:
        dom = conn.lookupByName(name)
        snapshots_name = list()
        for snapshot in dom.listAllSnapshots():
            if snapshot.isCurrent(): snapshots_name.insert(0, snapshot.getName())
            else : snapshots_name.append(snapshot.getName())
        return snapshots_name
    except libvirt.libvirtError:
        return make_response("<h1>libvirtError: Error when getting snapshot</h1>", 400)
    except Exception as e:
        return make_response("<h1>Unknown: Error when getting snapshot</h1>", 400)

def defineXML_domain(conn, request):
    # WARNING: Override existing domain with same UUID and name ! Can be used to update a Domain
    # TODO: Fonction pour créer un disque - TO CHECK
    try:
        domain_name = request.form['domain_name']
        cpu_allocated = request.form['cpu_allocated']
        ram_allocated = request.form['ram_allocated']
        disk_path = request.form['disk_path'] # Besoin d'autre chose que le path pour le disque ???
        iso_path = request.form['iso_path']
        vm_xml_description = f'''
        <domain type='kvm' id='40'>
            <name>{domain_name}</name>
            <memory unit='KiB'>{ram_allocated}</memory>
            <currentMemory unit='KiB'>{ram_allocated}</currentMemory>
            <vcpu placement='static'>{cpu_allocated}</vcpu>
            <os>
                <type arch='x86_64'>hvm</type>
                <boot dev='cdrom'/>
                <boot dev='hd'/>
            </os>
            <devices>
                <emulator>/usr/bin/qemu-system-x86_64</emulator>
                <disk type='file' device='disk'>
                    <driver name='qemu' type='qcow2'/>
                    <source file='{disk_path}' index='2' />
                    <target dev='vda' bus='virtio'/>
                </disk>
                <disk type='file' device='cdrom'>
                    <driver name='qemu' type='raw' index='1' />
                    <source file='{iso_path}'/>
                    <target dev='sda' bus='sata' />
                    <readonly/>
                </disk>
                <graphics type='vnc' port='5900' autoport='yes' listen='127.0.0.1'>
                    <listen type='address' address='127.0.0.1'/>
                </graphics>
                <audio id='1' type='none'/>
            </devices>
            <seclabel type='none' label="dac"/>
        </domain>
        '''
        """
        <pool type="netfs">
            <name>nfs</name>
            <source>
                <host name="172.19.16.142"/>
                <dir path="/mnt/nfs/" />
                <format type='nfs'/>
            </source>
            <target>
                <path>/var/lib/libvirt/images/vms_nfs</path>
            </target>
        </pool>
        <disk type='network' device='disk'>
            <driver name='qemu' type='qcow2'/>
            <source protocol='nfs' name='{disk_path}' index='2'>
                <host name='172.19.16.142'/>
            </source>
            <target dev='vda' bus='virtio'/>
        </disk>
        """
        conn.defineXML(vm_xml_description)
        return make_response("<h1>Success</h1>", 200)
    except libvirt.libvirtError:
        return make_response("<h1>libvirtError: Error when defining domain</h1>", 400)
    except Exception as e:
        print(e)
        return make_response("<h1>Unknown: Error when defining domain</h1>", 400)

def migrate_domain(conn, request):
    # Besoin d'avoir la vm allumée
    try:
        vm_name = request.form['vm_name']
        ip_dest = request.form['ip_dest']
        dom = conn.lookupByName(vm_name)
        dconn = get_connector_to_node(ip_dest)
        dom.migrate(dconn, flags=libvirt.VIR_MIGRATE_NON_SHARED_DISK)
    except libvirt.libvirtError:
        return make_response("<h1>libvirtError: Error when migrating domain</h1>", 400)
    except Exception as e:
        print(e)
        return make_response("<h1>Unknown: Error when migrating domain</h1>", 400)
