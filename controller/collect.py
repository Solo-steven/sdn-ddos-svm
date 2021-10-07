from ryu.base import app_manager
from ryu.controller.handler import DEAD_DISPATCHER, MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.controller import ofp_event
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp, icmp
from ryu.lib.packet import ether_types, in_proto
from ryu.lib import hub
import math, csv, os

class Controller(app_manager.RyuApp):
    OFP_VERSIONS = [ ofproto_v1_3.OFP_VERSION ]
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        # for L2Switch function
        self.mac_to_port_table = {}
        # for moniter traffic
        self.datapath_table = {}
        self.thread = hub.spawn(self._moniter)
        self.time_interval = 2
        # for data collection
        self.label = 0
        self.collect_count = 0
        self.max_data_count = 400
        # Create file if not exist
        if os.path.isfile("./model/data.csv"):
            with  open("./model/data.csv", "w", newline="") as f:
                f_writer = csv.writer(f)
                f_writer.writerow(["SSIP", "SSP", "SDFP", "SDFB", "SFE", "label"])

    """ ================================= """
    """ ========== Moniter 功能 ========== """
    """ ================================= """
    def log_flows_match(self, flows):
        for flow in flows:
            in_port = flow.match["in_port"]
            dst_eth = flow.match["eth_dst"]
            src_ip = flow.match["ipv4_src"]
            dst_ip = flow.match["ipv4_dst"]
            if flow.match['ip_proto'] == 1: # ICMP
                pass
            elif flow.match['ip_proto'] == 17:  # UDP 
                src_port = flow.match['udp_src']
                dst_port = flow.match['udp_dst']
            elif flow.match['ip_proto'] == 6: # TCP
                src_port  = flow.match['tcp_src']
                dst_port  = flow.match['tcp_dst']
            print("Eth Dst: {}. In Port {}. IP Src: {}. IP Dst: {}. Port Src: {}. Port Dst: {} "
                    .format(dst_eth, in_port, src_ip, dst_ip,src_port, dst_port ))

    def _moniter(self):
        while True:
            if self.collect_count > self.max_data_count:
                print("Collection Over")
                return
            for datapath in self.datapath_table.values():
                parser = datapath.ofproto_parser
                flow_req = parser.OFPFlowStatsRequest(datapath)
                datapath.send_msg(flow_req)
            hub.sleep(self.time_interval)
    @set_ev_cls(ofp_event.EventOFPStateChange, [ MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _handle_state_change(self, ev):
        if ev.state == MAIN_DISPATCHER:
            if ev.datapath not in self.datapath_table:
                print("[REGISTER SWITCH]:", ev.datapath.id)
                self.datapath_table[ev.datapath.id] = ev.datapath
        elif ev.state == DEAD_DISPATCHER:
            if ev.datapath in self.datapath_table:
                print("[DISCONNECT SWITCH]:", ev.datapath.id)
                del self.datapath_table[ev.datapath.id]
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _handle_flow_stats_reply(self, ev):
        flows = sorted([flow for flow in ev.msg.body if flow.priority == 1], key=lambda flow:(flow.match["in_port"]))
        if len(flows) != 0 :
            # print("[Flow Stats]")
            # self.log_flows_match(flows)
            self._flow_stats_collect(flows)
    
    """ ================================= """
    """  ========== collect 功能 ========== """
    """ ================================= """
    def _flow_stats_collect(self, flows):
        self.collect_count +=1 
        ip_src_set = set()
        ip_dst_set = set()
        port_src_set = set()
        port_dst_set = set()
        for flow in flows:
            ip_src_set.add(flow.match['ipv4_src'])
            ip_dst_set.add(flow.match['ipv4_dst'])
            if flow.match['ip_proto'] == 1: # ICMP
                pass
            elif flow.match['ip_proto'] == 17:  # UDP 
                port_src_set.add(flow.match['udp_src'])
                port_dst_set.add(flow.match['udp_dst'])
            elif flow.match['ip_proto'] == 6: # TCP
                port_src_set.add(flow.match['tcp_src'])
                port_dst_set.add(flow.match['tcp_dst'])
        SSIP = len(ip_src_set) / self.time_interval
        SSP = len(port_src_set) / self.time_interval

        total_pkt = 0
        total_byte = 0
        for flow in flows:
            total_pkt += flow.packet_count
            total_byte += flow.byte_count
        mean_pkt = total_pkt / len(flows)
        mean_byte = total_byte / len(flows)
        var_pkt = 0
        var_byte = 0
        for flow in flows:
            var_pkt += ((flow.packet_count - mean_pkt) **2)
            var_byte += ((flow.byte_count - mean_byte) **2)
        SDFP = math.sqrt(var_pkt)
        SDFB = math.sqrt(var_byte)

        SFE = len(flows) / self.time_interval
        # print("SSIP: {}, SSP: {}, SDFP:{}, SDFB: {}, SFE: {}"
        #         .format(SSIP, SSP, SDFP, SDFB, SFE))
        with open("./model/data.csv", "a", newline="") as f:
            f_writer = csv.writer(f)
            f_writer.writerow([SSIP, SSP, SDFP, SDFB, SFE, self.label])

    """ ================================= """
    """  ========== Switch 功能 ========== """
    """ ================================= """
    def _add_flow(self, datapath , match, priority, actions):
        # Get modules
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        # flow mod
        insts = [ parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions) ]
        flow_mod = parser.OFPFlowMod(datapath=datapath, match=match, priority=priority, instructions= insts)
        datapath.send_msg(flow_mod)
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _hanlde_switch_feature(self, ev):
        # Get modules
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        # Create a flow entry info
        match= parser.OFPMatch()
        actions = [ parser.OFPActionOutput(ofproto.OFPP_CONTROLLER) ]
        self._add_flow(datapath, match, 0 , actions)
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _handle_packet_in(self, ev):
        # Get modules and data
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        pkt = packet.Packet(ev.msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        in_port = ev.msg.match["in_port"]
        # L2Switch Logical (flow_mod邏輯抽離)
        self.mac_to_port_table.setdefault(datapath.id, {})
        self.mac_to_port_table[datapath.id][eth_pkt.src] = in_port
        if eth_pkt.dst in self.mac_to_port_table[datapath.id]:
            out_port = self.mac_to_port_table[datapath.id][eth_pkt.dst]
        else:
            out_port = ofproto.OFPP_FLOOD
        actions = [parser.OFPActionOutput(out_port)]
        pkt_out = parser.OFPPacketOut(
            datapath=datapath, 
            buffer_id= ofproto.OFP_NO_BUFFER,
            in_port=in_port,
            actions=actions,
            data = ev.msg.data
        )
        datapath.send_msg(pkt_out)
        # flow mod(增加ip或icmp、layer4 protocol)
        if out_port != ofproto.OFPP_FLOOD:
            if eth_pkt.ethertype == ether_types.ETH_TYPE_IP:
                ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
                if ipv4_pkt.proto ==in_proto.IPPROTO_ICMP:
                    icmp_pkt = pkt.get_protocol(icmp.icmp)
                    match = parser.OFPMatch(
                        in_port=in_port, eth_dst=eth_pkt.dst, eth_type=ether_types.ETH_TYPE_IP,
                        ipv4_src=ipv4_pkt.src, ipv4_dst=ipv4_pkt.dst, ip_proto = ipv4_pkt.proto,
                        icmpv4_code = icmp_pkt.code, icmpv4_type = icmp_pkt.type
                    )
                elif ipv4_pkt.proto == in_proto.IPPROTO_UDP:
                    udp_pkt = pkt.get_protocol(udp.udp)
                    match = parser.OFPMatch(
                        in_port=in_port, eth_dst=eth_pkt.dst, eth_type=ether_types.ETH_TYPE_IP,
                        ipv4_src=ipv4_pkt.src, ipv4_dst=ipv4_pkt.dst, ip_proto = ipv4_pkt.proto,
                        udp_src=udp_pkt.src_port, udp_dst=udp_pkt.dst_port,
                    )
                elif ipv4_pkt.proto == in_proto.IPPROTO_TCP:
                    tcp_pkt = pkt.get_protocol(tcp.tcp)
                    match = parser.OFPMatch(
                        in_port=in_port, eth_dst=eth_pkt.dst, eth_type=ether_types.ETH_TYPE_IP,
                        ipv4_src=ipv4_pkt.src, ipv4_dst=ipv4_pkt.dst, ip_proto = ipv4_pkt.proto,
                        tcp_src=tcp_pkt.src_port, tcp_dst=tcp_pkt.dst_port,
                    )
                self._add_flow(datapath, match, 1, actions)
