import sys, subprocess
from gi.repository import Gio, GLib
bus=Gio.bus_get_sync(Gio.BusType.SESSION,None)
iface='org.kde.StatusNotifierItem'
xml='''<node><interface name="org.kde.StatusNotifierItem">
<property name="Id" type="s" access="read"/><property name="Category" type="s" access="read"/>
<property name="Title" type="s" access="read"/><property name="Status" type="s" access="read"/>
<property name="IconName" type="s" access="read"/><property name="IconPixmap" type="a(iiay)" access="read"/>
<signal name="NewIcon"/></interface></node>'''
props={k:GLib.Variant('s',v) for k,v in dict(Id='Zoom',Category='ApplicationStatus',Title='Temporary override regression test',Status='Active',IconName='').items()}
props['IconPixmap']=GLib.Variant('a(iiay)',[(24,24,bytes([255,0,100,255])*24*24)])
bus.register_object('/StatusNotifierItem',Gio.DBusNodeInfo.new_for_xml(xml).interfaces[0],None,lambda *args:props[args[4]],None)
bus.call_sync('org.kde.StatusNotifierWatcher','/StatusNotifierWatcher','org.kde.StatusNotifierWatcher','RegisterStatusNotifierItem',GLib.Variant('(s)',('/StatusNotifierItem',)),None,0,3000,None)
loop=GLib.MainLoop(); phase=sys.argv[1]
def capture(label):
 subprocess.run(['grim','-g','650,0 620x65',f'/tmp/hyprlife-override-{phase}-{label}.png'],check=True)
def bitmap():
 capture('initial')
 props['IconPixmap']=GLib.Variant('a(iiay)',[(24,24,bytes([255,255,0,0])*24*24)])
 bus.emit_signal(None,'/StatusNotifierItem',iface,'NewIcon',None)
 return False
def named():
 capture('bitmap-update')
 props['IconName']=GLib.Variant('s','dialog-error')
 bus.emit_signal(None,'/StatusNotifierItem',iface,'NewIcon',None)
 return False
def finish():
 capture('name-update'); loop.quit();return False
GLib.timeout_add(1200,bitmap);GLib.timeout_add(2400,named);GLib.timeout_add(3600,finish);loop.run()
print('Completed override regression: initial -> bitmap update -> icon-name update')
