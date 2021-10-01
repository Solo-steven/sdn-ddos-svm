from mininet.net import Mininet 
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.topo import Topo
from mininet.cli import CLI
import sys, os, time

class NormalNetWork(Topo):
    def build(self):
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        h3 = self.addHost("h3")
        h4 = self.addHost("h4")
        s1 =self.addSwitch("s1", cls=OVSKernelSwitch, protocol="OpenFlow13")
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)
        self.addLink(h4, s1)

def attacker_host(host):
    pass
def victim_server(server):
    pass
def normal_host(host):
    pass

if __name__ == "__main__":
    # NetWork Setting
    if len(sys.argv) >=2:
        ip = sys.argv[1]
    else:
        ip = "127.0.0.1"
    c0 = RemoteController("c0", ip=ip, port=6653)
    net = Mininet(topo=NormalNetWork(), controller=c0)
    ## NetWork Start
    net.start()
    h1 = net.get("h1")
    h2 = net.get("h2")
    h3 = net.get("h3")
    h4 = net.get("h4")

    h1.cmd("cd ./Simple-Server && npm start & ")
    for count in range(1, 300):
        h2.cmd("curl --local-port 80 10.0.0.1:3000 &")
        h3.cmd("curl --local-port 80 10.0.0.1:3000 &")
        h4.cmd("curl --local-port 80 10.0.0.1:3000 &")
        time.sleep(2)
    CLI(net)
    net.stop()