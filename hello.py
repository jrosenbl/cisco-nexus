#!/usr/bin/python
#
# The functions defined below print various summaries to the users console or vty.  They have been developed and
# tested on the Titanium/N7K image in VIRL.  -- no guarantees for any other Nexus platforms.  Mainly I'm just
# playing around with the Python API as a learning exercise.

BOLD = '\033[1m'
UNBOLD = '\033[0;0m'
import re

def pp(cmd):
    """
    :param cmd: any CLI command
    :return: pretty prints the dictionary returned by clid(cmd)
    """
    cmd_out = clid(cmd)
    for k, v in cmd_out.items():
        print k, ': ', v

def hello():
    """ Greets with hostname, platform, software version and uptime """
    cmd = clid('show version')
    msg = '''
Hello!  My name is %s%s%s.
I'm a %s
running %s''' % (BOLD,cmd['host_name'],UNBOLD, cmd['chassis_id'], cmd['sys_ver_str'])
    print msg
    up = clid('show sys uptime')
    print "I've been working continously for %s days, %s hours, %s minutes, %s seconds\n" % \
          (up['sys_up_days'],up['sys_up_hrs'],up['sys_up_mins'],up['sys_up_secs'])

def summarize_interfaces():
    """ count modules by type, total ports and ports by type, total ports up """

    sh_vers = clid('show version')
    # get slot count from chassis description in show version (maybe a little 'ify')
    slot_count = int(sh_vers['chassis_id'].split(' ')[2][1:])
    mod_tbl = {}
    # clid('show module') does not return the whole table as you might expect.  So, it's necessary
    # to step through each slot.  might be easier to just use cli()
    # This loop builds a dictionary indexed by module type that counts the modules and ports by type.
    # It also sums the number of modules with status == 'ok'. Why not count the modules that are not ok, you ask?
    for slot_num in range(1,slot_count):
        sh_mod = clid('show mod %s' % slot_num)
        if not sh_mod:
            continue
        mod_type = sh_mod['TABLE_modinfo/model']
        mod_ports = sh_mod['TABLE_modinfo/ports']
        mod_status = sh_mod['TABLE_modinfo/status']

        if not (mod_type in mod_tbl):
            mod_tbl[mod_type] = {'mod_count':1,'port_count':int(mod_ports),'ok_count':1 if mod_status == 'ok' else 0}
        else:
            mod_tbl[mod_type]['mod_count'] += 1
            mod_tbl[mod_type]['port_count'] += int(mod_ports)
            mod_tbl[mod_type]['ok_count'] += 1 if mod_status == 'ok' else 0

    for mod_type in mod_tbl:
        mod_count = mod_tbl[mod_type]['mod_count']
        print mod_count, mod_type, 'module%s' % 's' if mod_count > 1 else '',
        if not mod_type.startswith('N7K-SUP'):
            print 'providing',mod_tbl[mod_type]['port_count'],'ports'
            if mod_tbl[mod_type]['ok_count'] < mod_count:
                print ' (%s modules are not OK)' % str(mod_count - mod_tbl[mod_type]['ok_count'])
        else:
            print

    # count all of the Eth ports in 'show int status' by speed and subtotal the number in 'connected' state
    ifc_count = {}
    tot_ifc_count = 0
    for l in cli('show int status').split('\n'):
        if l.startswith('Eth'):
            tot_ifc_count += 1
            f = l.split()
            speed = f[5]
            up = f[2] == 'connected'
            if up:
                try:
                    speed = int(speed)  # not sure what might show up here
                except ValueError, e:
                    print e
                    print 'speed = ',speed
                    break

                if speed in ifc_count:
                    ifc_count[speed]['count'] += 1
                else:
                    ifc_count[speed] = {'count':1}

    print tot_ifc_count,'total Ethernet ports'
    for i in ifc_count:
        if i >= 1000:
            speed = i/1000
            units = 'G'
        else:
            speed = i
            units = 'M'
        print "%3d %s%s ports are up" % (ifc_count[i]['count'],speed,units)

def neighbor_counter():
    """ tally the neighbors and create a list of neighbor interfaces """
    sh_cdp_neigh = cli('show cdp neigh')
    nbr_count = 0
    nbr_set = []
    nbr_ifc_set = []
    skip = True
    for l in sh_cdp_neigh.split('\n'):
        if len(l.rstrip()) == 0:  # skip blank lines
            continue
        if l.startswith('Device-ID'):  # skip lines until the column header line
            skip = False
            continue
        if not skip:
            fld = l.split()
            nbr_name = fld[0]
            nbr_ifc = fld[1]
            if not nbr_name in nbr_set:
                nbr_set.append(nbr_name)
            if not nbr_ifc in nbr_ifc_set:
                nbr_ifc_set.append(nbr_ifc)
    print '%s neighbors across the following interfaces:' % len(nbr_set)
    for i,ifc in enumerate(nbr_ifc_set):
        if i > 10:  # print 10 interfaces per line
            print
        print ifc,
    print
    # return len(nbr_set)

def route_counter():
    """ count the IPv4 routes """
    ip_routes = cli('show ip route det').split('\n')
    route_count = 0
    pat = re.compile('\d{1,3}\.\d{1,3}\.')
    for l in ip_routes:
        if re.match(pat,l):
            route_count += 1
    print route_count,"IPv4 routes in total"
    # return route_count

def intro():
    hello()
    print 'I have'
    summarize_interfaces()
    neighbor_counter()
    route_counter()



