import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import random
import queue
import re
from datetime import datetime


# --- Warna & Konstanta ---

BG_DARK      = "#0d1117"
BG_PANEL     = "#161b22"
BG_HEADER    = "#1f2937"
ACCENT_BLUE  = "#58a6ff"
ACCENT_GREEN = "#3fb950"
ACCENT_AMBER = "#d29922"
ACCENT_PURPLE= "#bc8cff"
TEXT_MAIN    = "#e6edf3"
TEXT_DIM     = "#8b949e"
TEXT_SUCCESS = "#3fb950"
TEXT_ERROR   = "#f85149"
BORDER_COLOR = "#30363d"

MODEL_COLORS = {
    "Request-Response": ACCENT_BLUE,
    "Publish-Subscribe": ACCENT_GREEN,
    "Message Passing":  ACCENT_AMBER,
    "RPC":              ACCENT_PURPLE,
}


def timestamp():
    now = datetime.now()
    return now.strftime("%H:%M:%S.") + f"{now.microsecond // 1000:03d}"


# --- Backend Simulasi ---

class SimulationBackend:
    """Menjalankan tiap model komunikasi di daemon thread dan mengirim
    hasilnya ke GUI via callback."""

    def __init__(self, log_callback, metrics_callback, flow_callback=None):
        self.log_cb     = log_callback
        self.metrics_cb = metrics_callback
        self.flow_cb    = flow_callback or (lambda src, dst, color: None)
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def reset(self):
        self._stop_flag = False

    # --- Request-Response ---
    def run_request_response(self, client_id: str, request_data: str):
        """Skenario e-commerce: User App → HTTP GET → Product API Server → JSON response."""
        self.reset()
        color = ACCENT_BLUE

        product_id  = request_data.replace(" ", "_").upper()
        endpoint    = f"/api/v1/products/{product_id}"
        http_method = "GET"

        def _simulate():
            start_time = time.time()
            msg_count  = 0

            self.log_cb(f"\n{'='*55}", color)
            self.log_cb(f"  MODEL: REQUEST-RESPONSE  [ E-Commerce REST API ]", color)
            self.log_cb(f"{'='*55}", color)
            time.sleep(0.3)

            self.log_cb(f"\n[{timestamp()}] 📤 USER-APP ({client_id}) → Menyusun HTTP Request...", color)
            self.log_cb(f"             {http_method} {endpoint}", TEXT_DIM)
            self.log_cb(f"             Headers: {{Authorization: Bearer eyJhb..., Accept: application/json}}", TEXT_DIM)
            time.sleep(0.5)

            self.log_cb(f"[{timestamp()}] 🔀 HTTP Request dikirim ke PRODUCT-API-SERVER...", color)
            self.flow_cb("CLIENT", "SERVER", color)
            msg_count += 1
            time.sleep(random.uniform(0.3, 0.7))

            self.log_cb(f"[{timestamp()}] 🖥️  PRODUCT-API-SERVER → Request diterima!", TEXT_MAIN)
            self.log_cb(f"             Routing: {http_method} {endpoint} → ProductController", TEXT_DIM)
            self.log_cb(f"             Query DB: SELECT * FROM products WHERE id='{product_id}'", TEXT_DIM)
            time.sleep(random.uniform(0.5, 1.0))

            price = random.randint(50, 999) * 1000
            stock = random.randint(0, 200)
            response_json = (
                f'{{"status":200, "data":{{"id":"{product_id}", '
                f'"name":"{request_data.title()}", "price":{price}, '
                f'"stock":{stock}, "available":{str(stock > 0).lower()}}}}}'
            )
            self.log_cb(f"[{timestamp()}] ✅ PRODUCT-API-SERVER → Response 200 OK siap!", TEXT_SUCCESS)
            self.log_cb(f"             Content-Type: application/json", TEXT_DIM)
            time.sleep(0.3)

            self.log_cb(f"[{timestamp()}] 🔀 HTTP Response dikirim ke USER-APP ({client_id})...", color)
            self.flow_cb("SERVER", "CLIENT", ACCENT_GREEN)
            msg_count += 1
            time.sleep(random.uniform(0.3, 0.6))

            self.log_cb(f"[{timestamp()}] 📥 USER-APP ({client_id}) → Response diterima & di-parse!", color)
            self.log_cb(f"             {response_json}", TEXT_SUCCESS)
            self.log_cb(f"             → Menampilkan detail produk ke halaman e-commerce.", TEXT_DIM)

            elapsed     = (time.time() - start_time) * 1000
            latency_net = random.randint(20, 80)
            self.log_cb(f"\n[{timestamp()}] 📊 METRIK:", TEXT_MAIN)
            self.log_cb(f"             Total Pesan  : {msg_count} (REQ + RES)", TEXT_DIM)
            self.log_cb(f"             Waktu Total  : {elapsed:.0f} ms", TEXT_DIM)
            self.log_cb(f"             Network Est. : ~{latency_net} ms", TEXT_DIM)
            self.log_cb(f"             Status       : SUKSES ✅", TEXT_SUCCESS)
            self.log_cb(f"{'='*55}\n", color)

            self.metrics_cb("Request-Response", {
                "messages": msg_count,
                "latency":  f"{latency_net} ms",
                "time":     f"{elapsed:.0f} ms",
                "pattern":  "1 REQ + 1 RES",
            })

        threading.Thread(target=_simulate, daemon=True).start()

    # --- Publish-Subscribe ---
    def run_publish_subscribe(self, topic: str, publisher: str, num_subscribers: int):
        """Skenario order event system: OrderService publish → RabbitMQ → fan-out ke service subscriber."""
        self.reset()
        color = ACCENT_GREEN

        service_names = [
            "NotificationService", "InventoryService", "InvoiceService",
            "AnalyticsService",    "ShippingService",
        ]

        def _simulate():
            start_time = time.time()
            msg_count  = 0
            subs       = service_names[:num_subscribers]
            order_id   = f"ORD-{random.randint(10000,99999)}"
            user_id    = f"USR-{random.randint(1000,9999)}"
            amount     = random.randint(1, 20) * 50000

            self.log_cb(f"\n{'='*55}", color)
            self.log_cb(f"  MODEL: PUBLISH-SUBSCRIBE  [ Order Event System ]", color)
            self.log_cb(f"{'='*55}", color)
            time.sleep(0.3)

            self.log_cb(f"\n[{timestamp()}] 📋 FASE SUBSCRIBE — Service mendaftar ke Message Broker", color)
            self.log_cb(f"             Broker : RabbitMQ  |  Exchange: order-events", TEXT_DIM)
            for sub in subs:
                if self._stop_flag:
                    return
                self.log_cb(f"[{timestamp()}] 🔔 {sub} → SUBSCRIBE  queue='{sub.lower()}-queue'  routing-key='{topic}'", color)
                msg_count += 1
                time.sleep(0.3)
            self.log_cb(f"[{timestamp()}] 🗄️  MESSAGE BROKER → {len(subs)} service terdaftar di exchange '{topic}'", TEXT_SUCCESS)
            time.sleep(0.4)

            self.log_cb(f"\n[{timestamp()}] 📢 FASE PUBLISH — {publisher} menerbitkan event", color)
            payload = (
                f'{{"event":"{topic}", "order_id":"{order_id}", '
                f'"user_id":"{user_id}", "total":{amount}, '
                f'"items":["SKU-A{random.randint(10,99)}","SKU-B{random.randint(10,99)}"], '
                f'"timestamp":"{timestamp()}", "status":"PENDING"}}'
            )
            self.log_cb(f"[{timestamp()}] 📣 {publisher} → PUBLISH  topic='{topic}'", color)
            self.log_cb(f"             Payload: {payload}", TEXT_DIM)
            self.flow_cb("PUBLISHER", "BROKER", color)
            msg_count += 1
            time.sleep(0.5)

            self.log_cb(f"\n[{timestamp()}] 🗄️  MESSAGE BROKER → Fan-out event ke {len(subs)} service...", TEXT_MAIN)
            time.sleep(0.3)

            action_map = {
                "NotificationService": f"Kirim email & push notif ke user {user_id}",
                "InventoryService":    f"Kurangi stok item order {order_id}",
                "InvoiceService":      f"Generate invoice PDF untuk {order_id}",
                "AnalyticsService":    f"Catat event penjualan Rp {amount:,}",
                "ShippingService":     f"Buat awb & jadwalkan pickup {order_id}",
            }
            sub_canvas = ["SUB-A", "SUB-B", "SUB-C"]
            for idx, sub in enumerate(subs):
                if self._stop_flag:
                    return
                delay = random.uniform(0.1, 0.4)
                time.sleep(delay)
                self.log_cb(f"[{timestamp()}] 📥 {sub} → Event diterima (delay: {delay*1000:.0f}ms)", color)
                self.log_cb(f"             → Aksi: {action_map.get(sub, 'Proses event')}", TEXT_DIM)
                if idx < len(sub_canvas):
                    self.flow_cb("BROKER", sub_canvas[idx], color)
                msg_count += 1

            elapsed = (time.time() - start_time) * 1000
            latency = random.randint(10, 40)
            self.log_cb(f"\n[{timestamp()}] 📊 METRIK:", TEXT_MAIN)
            self.log_cb(f"             Total Pesan  : {msg_count}", TEXT_DIM)
            self.log_cb(f"             Subscriber   : {len(subs)} service", TEXT_DIM)
            self.log_cb(f"             Network Est. : ~{latency} ms/delivery", TEXT_DIM)
            self.log_cb(f"             Waktu Total  : {elapsed:.0f} ms", TEXT_DIM)
            self.log_cb(f"             Status       : SUKSES ✅", TEXT_SUCCESS)
            self.log_cb(f"{'='*55}\n", color)

            self.metrics_cb("Publish-Subscribe", {
                "messages": msg_count,
                "latency":  f"{latency} ms/delivery",
                "time":     f"{elapsed:.0f} ms",
                "pattern":  f"1 PUB → {len(subs)} SUB",
            })

        threading.Thread(target=_simulate, daemon=True).start()

    # --- Message Passing ---
    def run_message_passing(self, nodes: list, chain_mode: bool):
        """Skenario microservice pipeline: chain bertahap atau broadcast config ke semua node."""
        self.reset()
        color    = ACCENT_AMBER
        mode_str = "CHAIN (Berantai)" if chain_mode else "BROADCAST"

        def _simulate():
            start_time = time.time()
            msg_count  = 0

            self.log_cb(f"\n{'='*55}", color)
            self.log_cb(f"  MODEL: MESSAGE PASSING  [ Microservice Pipeline ]", color)
            self.log_cb(f"  Mode: {mode_str}", color)
            self.log_cb(f"{'='*55}", color)
            time.sleep(0.3)

            if chain_mode:
                req_id  = f"REQ-{random.randint(10000,99999)}"
                payload = (
                    f'{{"req_id":"{req_id}", "action":"process_order", '
                    f'"user_id":"USR-{random.randint(100,999)}", '
                    f'"cart_total":{random.randint(1,50)*25000}}}'
                )
                self.log_cb(f"\n[{timestamp()}] 🔗 Mode CHAIN — Pipeline pemrosesan request", color)
                self.log_cb(f"[{timestamp()}] 📦 {nodes[0]} → Menerima request dari client", color)
                self.log_cb(f"             Payload: {payload}", TEXT_DIM)
                time.sleep(0.3)

                hop_actions = [
                    "Validasi token JWT & autorisasi user",
                    "Validasi stok & kalkulasi harga akhir",
                    "Proses transaksi & update status order",
                    "Persist data ke database & generate receipt",
                    "Audit log & kirim konfirmasi ke message queue",
                ]
                canvas_chain = ["NODE-A", "NODE-B", "NODE-C", "NODE-D"]
                for i in range(len(nodes) - 1):
                    if self._stop_flag:
                        return
                    delay = random.uniform(0.3, 0.6)
                    time.sleep(delay)
                    msg_count += 1
                    action = hop_actions[i] if i < len(hop_actions) else "Proses & teruskan pesan"
                    self.log_cb(
                        f"[{timestamp()}] 📨 {nodes[i]} → {nodes[i+1]}  "
                        f"[hop #{i+1}, delay: {delay*1000:.0f}ms]", color
                    )
                    self.log_cb(f"             Tugas  : {action}", TEXT_DIM)
                    self.log_cb(f"             Data   : {payload}", TEXT_DIM)
                    if i + 1 < len(canvas_chain):
                        self.flow_cb(canvas_chain[i], canvas_chain[i + 1], color)

                self.log_cb(f"[{timestamp()}] 🏁 {nodes[-1]} → Pipeline selesai! Request berhasil diproses.", TEXT_SUCCESS)

            else:
                cfg_version = f"v1.{random.randint(0,9)}.{random.randint(0,99)}"
                payload = (
                    f'{{"type":"CONFIG_RELOAD", "version":"{cfg_version}", '
                    f'"changed_keys":["rate_limit","timeout_ms","feature_flags"], '
                    f'"issued_at":"{timestamp()}", "issuer":"{nodes[0]}"}}'
                )
                self.log_cb(f"\n[{timestamp()}] 📡 Mode BROADCAST — Config change propagation", color)
                self.log_cb(f"[{timestamp()}] 📦 {nodes[0]} → Membuat config broadcast ({cfg_version})", color)
                self.log_cb(f"             {payload}", TEXT_DIM)
                time.sleep(0.3)

                threads_done = []
                for node in nodes[1:]:
                    def send_to(n):
                        delay = random.uniform(0.2, 0.8)
                        time.sleep(delay)
                        self.log_cb(
                            f"[{timestamp()}] 📨 {nodes[0]} → {n}  [delay: {delay*1000:.0f}ms]", color
                        )
                        self.log_cb(f"             CONFIG_RELOAD {cfg_version} diterima — {n} reload konfigurasi.", TEXT_DIM)
                        threads_done.append(n)
                    threading.Thread(target=send_to, args=(node,), daemon=True).start()
                    msg_count += 1

                waited = 0.0
                while len(threads_done) < len(nodes) - 1 and waited < 3.0:
                    time.sleep(0.1); waited += 0.1

                self.log_cb(f"[{timestamp()}] ✅ Config {cfg_version} berhasil disebarkan ke {len(nodes)-1} service!", TEXT_SUCCESS)

            elapsed = (time.time() - start_time) * 1000
            latency = random.randint(30, 90)
            self.log_cb(f"\n[{timestamp()}] 📊 METRIK:", TEXT_MAIN)
            self.log_cb(f"             Total Pesan  : {msg_count}", TEXT_DIM)
            self.log_cb(f"             Jumlah Node  : {len(nodes)} microservice", TEXT_DIM)
            self.log_cb(f"             Network Est. : ~{latency} ms/hop", TEXT_DIM)
            self.log_cb(f"             Waktu Total  : {elapsed:.0f} ms", TEXT_DIM)
            self.log_cb(f"             Mode         : {mode_str}", TEXT_DIM)
            self.log_cb(f"             Status       : SUKSES ✅", TEXT_SUCCESS)
            self.log_cb(f"{'='*55}\n", color)

            self.metrics_cb("Message Passing", {
                "messages": msg_count,
                "latency":  f"{latency} ms/hop",
                "time":     f"{elapsed:.0f} ms",
                "pattern":  mode_str,
            })

        threading.Thread(target=_simulate, daemon=True).start()

    # --- RPC ---
    def run_rpc(self, client_id: str, procedure: str, args: str):
        """Skenario gRPC backend call: caller → Protobuf serialize → HTTP/2 → remote service → return."""
        self.reset()
        color = ACCENT_PURPLE

        service_map = {
            "calculate_sum":   ("PaymentService",      "grpc://payment-svc:50051",  "BillingRPC.CalculateTotal"),
            "get_user_info":   ("UserService",          "grpc://user-svc:50052",     "UserRPC.GetProfile"),
            "process_data":    ("DataPipelineService",  "grpc://pipeline-svc:50053", "PipelineRPC.Transform"),
            "check_inventory": ("InventoryService",     "grpc://inventory-svc:50054","InventoryRPC.CheckStock"),
        }
        svc_name, svc_addr, rpc_method = service_map.get(
            procedure, ("RemoteService", "grpc://remote-svc:50055", f"ServiceRPC.{procedure}")
        )

        def _simulate():
            start_time = time.time()
            msg_count  = 0
            trace_id   = f"{random.randint(0xABCD, 0xFFFF):04X}-{random.randint(0x1000,0xFFFF):04X}"

            self.log_cb(f"\n{'='*55}", color)
            self.log_cb(f"  MODEL: REMOTE PROCEDURE CALL (gRPC)", color)
            self.log_cb(f"  Caller: {client_id}  →  Target: {svc_name}", color)
            self.log_cb(f"{'='*55}", color)
            time.sleep(0.3)

            self.log_cb(f"\n[{timestamp()}] 💻 {client_id} → Memanggil {rpc_method}({args})", color)
            self.log_cb(f"             (Tampak seperti local method call di code)", TEXT_DIM)
            self.log_cb(f"             Trace-ID: {trace_id}", TEXT_DIM)
            time.sleep(0.4)

            self.log_cb(f"[{timestamp()}] 🔧 gRPC CLIENT STUB → Serialize parameter ke Protobuf...", color)
            self.log_cb(f"             Input  : {procedure}Request{{args: [{args}]}}", TEXT_DIM)
            self.log_cb(
                f"             Binary : [0x{random.randint(0x10,0xFF):02X}, "
                f"0x{random.randint(0x10,0xFF):02X}, 0x{random.randint(0x10,0xFF):02X}, ...] "
                f"({random.randint(48,256)} bytes)", TEXT_DIM
            )
            self.flow_cb("CLIENT", "CLIENT\nSTUB", color)
            msg_count += 1
            time.sleep(0.5)

            self.log_cb(f"[{timestamp()}] 🌐 HTTP/2 → {client_id} → {svc_addr}", TEXT_MAIN)
            self.log_cb(f"             Method : POST /{rpc_method}", TEXT_DIM)
            self.log_cb(f"             Headers: {{content-type: application/grpc, trace-id: {trace_id}}}", TEXT_DIM)
            net_delay = random.uniform(0.4, 0.9)
            time.sleep(net_delay)
            self.log_cb(f"             Network delay: {net_delay*1000:.0f} ms  (HTTP/2 multiplexed)", TEXT_DIM)
            self.flow_cb("CLIENT\nSTUB", "SERVER\nSTUB", color)

            self.log_cb(f"[{timestamp()}] 🔧 gRPC SERVER STUB ({svc_name}) → Deserialize Protobuf → parameter...", color)
            self.flow_cb("SERVER\nSTUB", "SERVER", color)
            time.sleep(0.3)

            self.log_cb(f"[{timestamp()}] ⚙️  {svc_name} → Menjalankan {rpc_method}...", TEXT_MAIN)
            time.sleep(random.uniform(0.5, 1.2))

            proc_map = {
                "calculate_sum":   lambda a: f'{{"total":{sum(int(x.strip()) for x in a.split(",") if x.strip().isdigit())}, "currency":"IDR", "tax":0.11}}',
                "get_user_info":   lambda a: f'{{"user_id":"{a}", "name":"User_{a}", "tier":"premium", "status":"active"}}',
                "process_data":    lambda a: f'{{"job_id":"JOB-{random.randint(1000,9999)}", "output":"{a.upper()}_PROCESSED", "duration_ms":{random.randint(10,200)}}}',
                "check_inventory": lambda a: f'{{"sku":"{a}", "warehouse":"JKT-01", "stock":{random.randint(0,100)}, "reserved":{random.randint(0,10)}, "available":true}}',
            }
            result = proc_map[procedure](args) if procedure in proc_map else \
                f'{{"call_id":"{trace_id}", "return_code":0, "value":{random.randint(1000, 9999)}}}'

            self.log_cb(f"[{timestamp()}] ✅ {svc_name} → Eksekusi selesai, menyusun response...", TEXT_SUCCESS)
            self.log_cb(f"             Result : {result}", TEXT_DIM)
            time.sleep(0.3)

            self.log_cb(f"[{timestamp()}] 🔧 gRPC SERVER STUB → Serialize result ke Protobuf...", color)
            self.flow_cb("SERVER", "SERVER\nSTUB", TEXT_DIM)
            time.sleep(0.3)
            self.log_cb(f"[{timestamp()}] 🌐 HTTP/2 → {svc_addr} → {client_id}  (gRPC response)", TEXT_MAIN)
            self.flow_cb("SERVER\nSTUB", "CLIENT\nSTUB", TEXT_DIM)
            msg_count += 1
            time.sleep(net_delay * 0.8)

            self.log_cb(f"[{timestamp()}] 🔧 gRPC CLIENT STUB → Deserialize response Protobuf...", color)
            self.flow_cb("CLIENT\nSTUB", "CLIENT", TEXT_DIM)
            time.sleep(0.2)
            self.log_cb(f"[{timestamp()}] 💻 {client_id} → {rpc_method} SELESAI! (blocking call returned)", color)
            self.log_cb(f"             Return : {result}", TEXT_SUCCESS)
            self.log_cb(f"             → Lanjutkan proses bisnis dengan data dari {svc_name}.", TEXT_DIM)

            elapsed  = (time.time() - start_time) * 1000
            overhead = random.randint(15, 35)
            self.log_cb(f"\n[{timestamp()}] 📊 METRIK:", TEXT_MAIN)
            self.log_cb(f"             Total Pesan  : {msg_count} (CALL + RETURN)", TEXT_DIM)
            self.log_cb(f"             Network Est. : ~{net_delay*1000:.0f} ms × 2", TEXT_DIM)
            self.log_cb(f"             Protobuf OH  : ~{overhead} ms (serialize + deserialize)", TEXT_DIM)
            self.log_cb(f"             Waktu Total  : {elapsed:.0f} ms", TEXT_DIM)
            self.log_cb(f"             Transparan   : Ya (seperti local method call)", TEXT_DIM)
            self.log_cb(f"             Status       : SUKSES ✅", TEXT_SUCCESS)
            self.log_cb(f"{'='*55}\n", color)

            self.metrics_cb("RPC", {
                "messages": msg_count,
                "latency":  f"{net_delay*1000:.0f} ms × 2",
                "time":     f"{elapsed:.0f} ms",
                "pattern":  "CALL + RETURN + Protobuf",
            })

        threading.Thread(target=_simulate, daemon=True).start()


# --- Canvas Diagram Arsitektur ---

class ArchitectureCanvas(tk.Canvas):
    """Canvas yang menggambar diagram node-panah dan animasi dot bergerak."""

    NODE_W = 90
    NODE_H = 40

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_DARK, highlightthickness=0, **kwargs)
        self.nodes      = {}
        self.arrows     = []
        self.node_items = {}
        self._anim_id   = None
        self._flow_jobs = []
        self._current_model = None
        self.bind("<Configure>", lambda e: self._redraw())

    def draw_model(self, model: str):
        self._cancel_flow_jobs()
        self._current_model = model
        self.delete("all")
        self.nodes = {}; self.arrows = []; self.node_items = {}

        w = self.winfo_width()  or 500
        h = self.winfo_height() or 260

        dispatch = {
            "Request-Response": self._draw_req_res,
            "Publish-Subscribe": self._draw_pub_sub,
            "Message Passing":  self._draw_msg_passing,
            "RPC":              self._draw_rpc,
        }
        if model in dispatch:
            dispatch[model](w, h)

    def _cancel_flow_jobs(self):
        for jid in self._flow_jobs:
            try: self.after_cancel(jid)
            except Exception: pass
        self._flow_jobs.clear()
        self.delete("flow_dot")

    def _redraw(self):
        if self._current_model:
            self.draw_model(self._current_model)

    # --- Animasi dot ---
    def animate_flow(self, src: str, dst: str, color: str):
        """Gerakkan lingkaran bercahaya dari node src ke dst mengikuti arah panah."""
        if src not in self.nodes or dst not in self.nodes:
            return

        x1, y1 = self.nodes[src]
        x2, y2 = self.nodes[dst]
        nw2 = self.NODE_W // 2
        if x2 > x1:   x1 += nw2; x2 -= nw2
        elif x2 < x1: x1 -= nw2; x2 += nw2

        STEPS = 30; STEP_MS = 18; RADIUS = 7; GLOW_R = 12
        tag  = "flow_dot"
        glow = self.create_oval(x1-GLOW_R, y1-GLOW_R, x1+GLOW_R, y1+GLOW_R,
                                fill=color, outline="", stipple="gray50", tags=tag)
        dot  = self.create_oval(x1-RADIUS, y1-RADIUS, x1+RADIUS, y1+RADIUS,
                                fill=color, outline=TEXT_MAIN, width=1, tags=tag)

        def _step(step):
            if step > STEPS:
                try: self.delete(glow); self.delete(dot)
                except Exception: pass
                return
            t  = step / STEPS
            cx = x1 + (x2 - x1) * t
            cy = y1 + (y2 - y1) * t
            try:
                self.coords(glow, cx-GLOW_R, cy-GLOW_R, cx+GLOW_R, cy+GLOW_R)
                self.coords(dot,  cx-RADIUS,  cy-RADIUS,  cx+RADIUS,  cy+RADIUS)
                self.tag_raise(glow); self.tag_raise(dot)
            except Exception:
                return
            self._flow_jobs.append(self.after(STEP_MS, lambda s=step+1: _step(s)))

        _step(0)

    # --- Helper gambar ---
    def _draw_node(self, name: str, x: int, y: int, color: str, icon: str = ""):
        nw, nh = self.NODE_W, self.NODE_H
        self.create_rectangle(x-nw//2+3, y-nh//2+3, x+nw//2+3, y+nh//2+3,
                               fill="#000000", outline="", tags="shadow")
        r = self.create_rectangle(x-nw//2, y-nh//2, x+nw//2, y+nh//2,
                                   fill=color, outline=TEXT_MAIN, width=1.5, tags="node")
        t = self.create_text(x, y, text=f"{icon} {name}" if icon else name,
                              fill=TEXT_MAIN, font=("Courier", 9, "bold"), tags="node")
        self.nodes[name] = (x, y)
        self.node_items[name] = [r, t]
        return r, t

    def _draw_arrow(self, src: str, dst: str, label: str = "", color: str = TEXT_MAIN,
                    dashed: bool = False, offset_y: int = 0):
        if src not in self.nodes or dst not in self.nodes:
            return
        x1, y1 = self.nodes[src]; x2, y2 = self.nodes[dst]
        y1 += offset_y; y2 += offset_y
        nw2 = self.NODE_W // 2
        if x2 > x1:   x1 += nw2; x2 -= nw2
        elif x2 < x1: x1 -= nw2; x2 += nw2
        aid = self.create_line(x1, y1, x2, y2, fill=color, width=2,
                                arrow=tk.LAST, arrowshape=(10, 12, 4),
                                dash=(5,3) if dashed else (), tags="arrow")
        if label:
            self.create_text((x1+x2)//2, (y1+y2)//2 - 10, text=label,
                             fill=color, font=("Courier", 8), tags="arrow")
        self.arrows.append(aid)

    # --- Layout tiap model ---
    def _draw_req_res(self, w, h):
        cy = h // 2
        self._draw_node("CLIENT", w//4,   cy, "#1a3a5c", "💻")
        self._draw_node("SERVER", 3*w//4, cy, "#1a3a5c", "🖥️")
        self._draw_arrow("CLIENT", "SERVER", "REQUEST →",  ACCENT_BLUE,  offset_y=-18)
        self._draw_arrow("SERVER", "CLIENT", "← RESPONSE", ACCENT_GREEN, dashed=True, offset_y=18)
        self.create_text(w//2, h-20, text="[ Sinkron | 1-to-1 | Blocking ]",
                         fill=TEXT_DIM, font=("Courier", 8))

    def _draw_pub_sub(self, w, h):
        bx, by = w//2, h//2
        self._draw_node("PUBLISHER", w//6,    h//2,    "#1a3a2a", "📣")
        self._draw_node("BROKER",    bx, by,            "#2a2a1a", "🗄️")
        self._draw_node("SUB-A",     5*w//6,  h//4,    "#1a2a3a", "🔔")
        self._draw_node("SUB-B",     5*w//6,  h//2,    "#1a2a3a", "🔔")
        self._draw_node("SUB-C",     5*w//6,  3*h//4,  "#1a2a3a", "🔔")
        self._draw_arrow("PUBLISHER", "BROKER", "PUBLISH", ACCENT_GREEN)
        for sub in ("SUB-A", "SUB-B", "SUB-C"):
            self._draw_arrow("BROKER", sub, "→", ACCENT_GREEN)
        self.create_text(w//2, h-18, text="[ Asinkron | 1-to-Many | Decoupled ]",
                         fill=TEXT_DIM, font=("Courier", 8))

    def _draw_msg_passing(self, w, h):
        spacing = (w - 40) // 4
        nodes   = [("NODE-A","📦"), ("NODE-B","📦"), ("NODE-C","📦"), ("NODE-D","📦")]
        cy = h // 2
        for i, (name, icon) in enumerate(nodes):
            self._draw_node(name, 20 + spacing//2 + i*spacing, cy, "#2a1a1a", icon)
        for i in range(len(nodes) - 1):
            self._draw_arrow(nodes[i][0], nodes[i+1][0], "MSG", ACCENT_AMBER)
        self.create_text(w//2, h-18,
                         text="[ Asinkron | Point-to-Point | Chain/Broadcast ]",
                         fill=TEXT_DIM, font=("Courier", 8))

    def _draw_rpc(self, w, h):
        cy = h // 2
        xs = [w//8, 3*w//8, 5*w//8, 7*w//8]
        self._draw_node("CLIENT",      xs[0], cy, "#1a1a3a", "💻")
        self._draw_node("CLIENT\nSTUB",xs[1], cy, "#2a1a3a", "🔧")
        self._draw_node("SERVER\nSTUB",xs[2], cy, "#2a1a3a", "🔧")
        self._draw_node("SERVER",      xs[3], cy, "#1a1a3a", "🖥️")
        self._draw_arrow("CLIENT",       "CLIENT\nSTUB", "call",      ACCENT_PURPLE, offset_y=-14)
        self._draw_arrow("CLIENT\nSTUB", "SERVER\nSTUB", "network →", ACCENT_PURPLE, offset_y=-14)
        self._draw_arrow("SERVER\nSTUB", "SERVER",       "invoke",    ACCENT_PURPLE, offset_y=-14)
        self._draw_arrow("SERVER",       "SERVER\nSTUB", "return",    TEXT_DIM, dashed=True, offset_y=14)
        self._draw_arrow("SERVER\nSTUB", "CLIENT\nSTUB", "← result", TEXT_DIM, dashed=True, offset_y=14)
        self._draw_arrow("CLIENT\nSTUB", "CLIENT",       "value",     TEXT_DIM, dashed=True, offset_y=14)
        self.create_text(w//2, h-18,
                         text="[ Transparan | Marshal/Unmarshal | Seperti Local Call ]",
                         fill=TEXT_DIM, font=("Courier", 8))


# --- Panel Metrik & Analisis ---

class MetricsPanel(tk.Frame):
    """Tabel perbandingan performa + analisis otomatis dari semua model yang sudah berjalan."""

    COLUMNS = ["Model", "Total Pesan", "Latency Est.", "Waktu Total", "Pola"]

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_PANEL, **kwargs)
        self._data = {}
        self._build()

    def _build(self):
        tk.Label(self, text="📊  PERBANDINGAN PERFORMA MODEL KOMUNIKASI",
                 bg=BG_PANEL, fg=TEXT_MAIN, font=("Courier", 10, "bold"), pady=8).pack(fill=tk.X)
        tk.Frame(self, bg=BORDER_COLOR, height=1).pack(fill=tk.X, padx=8)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
                         background=BG_DARK, foreground=TEXT_MAIN,
                         rowheight=28, fieldbackground=BG_DARK, font=("Courier", 9))
        style.configure("Dark.Treeview.Heading",
                         background=BG_HEADER, foreground=ACCENT_BLUE,
                         font=("Courier", 9, "bold"), relief="flat")
        style.map("Dark.Treeview",
                  background=[("selected", "#264f78")],
                  foreground=[("selected", "#ffffff")])

        frame = tk.Frame(self, bg=BG_PANEL)
        frame.pack(fill=tk.X, expand=False, padx=8, pady=(4, 4))

        self.tree = ttk.Treeview(frame, columns=self.COLUMNS, show="headings",
                                  style="Dark.Treeview", height=4)
        for col, width in zip(self.COLUMNS, [145, 110, 115, 110, 175]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(self, text="ℹ️  Nilai latensi bersifat estimasi simulasi (bukan pengukuran jaringan nyata)",
                 bg=BG_PANEL, fg=TEXT_DIM, font=("Courier", 8), pady=4).pack()

        tk.Frame(self, bg=BORDER_COLOR, height=1).pack(fill=tk.X, padx=8, pady=(2, 0))
        tk.Label(self, text="🧠  ANALISIS PERBANDINGAN OTOMATIS",
                 bg=BG_PANEL, fg=ACCENT_AMBER,
                 font=("Courier", 9, "bold"), pady=5).pack(anchor="w", padx=10)

        self.analysis_box = tk.Text(
            self, bg=BG_DARK, fg=TEXT_MAIN, font=("Courier", 8),
            relief="flat", wrap=tk.WORD, height=6, state=tk.DISABLED,
            padx=8, pady=6, insertbackground=TEXT_MAIN, selectbackground="#264f78",
        )
        self.analysis_box.pack(fill=tk.X, padx=8, pady=(0, 8))
        for tag, col in [("highlight", ACCENT_AMBER), ("good", ACCENT_GREEN),
                         ("warn", ACCENT_BLUE), ("rpc", ACCENT_PURPLE), ("dim", TEXT_DIM)]:
            self.analysis_box.tag_configure(tag, foreground=col)

    def _parse_ms(self, val: str) -> float:
        m = re.search(r'[\d.]+', str(val))
        return float(m.group()) if m else 0.0

    def _generate_analysis(self) -> list:
        """Buat kalimat perbandingan dari semua model yang sudah dijalankan."""
        d = self._data
        if not d:
            return [("Belum ada data simulasi. Jalankan minimal satu model terlebih dahulu.", "dim")]

        lines = []
        ran   = list(d.keys())

        times = {m: self._parse_ms(d[m].get("time", "0")) for m in ran}
        if len(times) > 1:
            fastest = min(times, key=times.get)
            slowest = max(times, key=times.get)
            lines += [("⏱  Waktu total: ", "dim"), (fastest, "good"),
                      (f" tercepat ({times[fastest]:.0f} ms), ", "dim"), (slowest, "warn"),
                      (f" terlambat ({times[slowest]:.0f} ms).\n", "dim")]

        msgs = {m: int(d[m].get("messages", 0)) for m in ran}
        if len(msgs) > 1:
            fewest = min(msgs, key=msgs.get)
            most   = max(msgs, key=msgs.get)
            lines += [("📨  Pesan: ", "dim"), (fewest, "good"),
                      (f" paling hemat ({msgs[fewest]} msg); ", "dim"), (most, "warn"),
                      (f" paling banyak ({msgs[most]} msg).\n", "dim")]

        insight_map = {
            "Request-Response":  ("Ideal untuk operasi CRUD sinkron (REST API).",  "warn"),
            "Publish-Subscribe": ("Paling efisien untuk distribusi 1-to-many & decoupling service.", "good"),
            "Message Passing":   ("Cocok untuk pipeline bertahap antar microservice.", "highlight"),
            "RPC":               ("Overhead tertinggi (Protobuf marshal), tapi transparan bagi programmer.", "rpc"),
        }
        for m in ran:
            if m in insight_map:
                txt, tag = insight_map[m]
                lines += [(f"● {m}: ", tag), (f"{txt}\n", "dim")]

        if len(ran) == 4:
            lines += [("\n💡 Rekomendasi: ", "highlight"),
                      ("Gunakan Pub-Sub untuk notifikasi massal, ", "dim"),
                      ("RPC untuk query internal lintas service.", "dim")]
        return lines

    def update_metrics(self, model: str, data: dict):
        """Update tabel dan analisis otomatis setiap kali model selesai berjalan."""
        self._data[model] = data
        for row in self.tree.get_children():
            self.tree.delete(row)

        colors_tag = {
            "Request-Response": ACCENT_BLUE, "Publish-Subscribe": ACCENT_GREEN,
            "Message Passing":  ACCENT_AMBER, "RPC": ACCENT_PURPLE,
        }
        row_bg_even = "#131921"
        row_bg_odd  = "#0d1117"
        for idx, m in enumerate(["Request-Response", "Publish-Subscribe", "Message Passing", "RPC"]):
            if m in self._data:
                d   = self._data[m]
                tag = m.replace(" ", "_").replace("-", "_")
                self.tree.insert("", tk.END, values=(
                    m, d.get("messages","-"), d.get("latency","-"),
                    d.get("time","-"), d.get("pattern","-"),
                ), tags=(tag,))
                self.tree.tag_configure(tag,
                    foreground=colors_tag.get(m, TEXT_MAIN),
                    background=row_bg_even if idx % 2 == 0 else row_bg_odd)

        self.analysis_box.config(state=tk.NORMAL)
        self.analysis_box.delete("1.0", tk.END)
        for text, tag in self._generate_analysis():
            self.analysis_box.insert(tk.END, text, tag)
        self.analysis_box.config(state=tk.DISABLED)


# --- Main Application ---

class DistributedSimApp(tk.Tk):
    """Window utama: sidebar kontrol kiri, canvas + log tengah, metrik bawah."""

    def __init__(self):
        super().__init__()
        self.title("Simulasi Model Komunikasi Sistem Terdistribusi")
        self.geometry("1150x780")
        self.minsize(900, 650)
        self.configure(bg=BG_DARK)

        self._log_queue = queue.Queue()
        self.backend = SimulationBackend(
            log_callback     = self._enqueue_log,
            metrics_callback = self._on_metrics_update,
            flow_callback    = self._enqueue_flow,
        )
        self._build_ui()
        self._poll_log_queue()

    def _build_ui(self):
        self._build_title_bar()
        main = tk.Frame(self, bg=BG_DARK)
        main.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
        self._build_sidebar(main)
        self._build_center(main)

    def _build_title_bar(self):
        bar = tk.Frame(self, bg=BG_HEADER, pady=10)
        bar.pack(fill=tk.X)
        tk.Label(bar, text="⚡  SIMULASI INTERAKTIF — MODEL KOMUNIKASI SISTEM TERDISTRIBUSI",
                 bg=BG_HEADER, fg=ACCENT_BLUE, font=("Courier", 13, "bold")).pack(side=tk.LEFT, padx=16)
        tk.Label(bar, text="Sistem Terdistribusi",
                 bg=BG_HEADER, fg=TEXT_DIM, font=("Courier", 9)).pack(side=tk.RIGHT, padx=16)

    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=BG_PANEL, width=240, relief="flat",
                           bd=1, highlightthickness=1, highlightbackground=BORDER_COLOR)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6), pady=6)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="⚙  KONTROL SIMULASI",
                 bg=BG_PANEL, fg=ACCENT_BLUE, font=("Courier", 10, "bold"), pady=10).pack(fill=tk.X)
        tk.Frame(sidebar, bg=BORDER_COLOR, height=1).pack(fill=tk.X, padx=8)

        tk.Label(sidebar, text="Pilih Model Komunikasi:",
                 bg=BG_PANEL, fg=TEXT_DIM, font=("Courier", 8)).pack(padx=10, anchor="w", pady=(10, 2))

        self.model_var = tk.StringVar(value="Request-Response")
        style = ttk.Style()
        style.configure("Dark.TCombobox", fieldbackground=BG_DARK, background=BG_DARK,
                         foreground=TEXT_MAIN, arrowcolor=ACCENT_BLUE)
        self.model_combo = ttk.Combobox(
            sidebar, textvariable=self.model_var, state="readonly",
            values=["Request-Response", "Publish-Subscribe", "Message Passing", "RPC"],
            font=("Courier", 9), style="Dark.TCombobox"
        )
        self.model_combo.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.model_combo.bind("<<ComboboxSelected>>", self._on_model_change)

        tk.Frame(sidebar, bg=BORDER_COLOR, height=1).pack(fill=tk.X, padx=8)
        tk.Label(sidebar, text="Parameter:", bg=BG_PANEL, fg=TEXT_DIM,
                 font=("Courier", 8)).pack(padx=10, anchor="w", pady=(8, 2))

        self.param_frame = tk.Frame(sidebar, bg=BG_PANEL)
        self.param_frame.pack(fill=tk.X, padx=10)
        self._build_param_widgets()

        tk.Frame(sidebar, bg=BORDER_COLOR, height=1).pack(fill=tk.X, padx=8, pady=8)
        self.run_btn = tk.Button(sidebar, text="▶  JALANKAN SIMULASI",
                                  bg=ACCENT_BLUE, fg=BG_DARK, font=("Courier", 9, "bold"),
                                  relief="flat", cursor="hand2", activebackground="#3a7bd5",
                                  command=self._run_simulation, pady=8)
        self.run_btn.pack(fill=tk.X, padx=10, pady=2)
        tk.Button(sidebar, text="🗑  BERSIHKAN LOG",
                  bg=BG_HEADER, fg=TEXT_DIM, font=("Courier", 9),
                  relief="flat", cursor="hand2",
                  command=self._clear_log, pady=6).pack(fill=tk.X, padx=10, pady=2)

        tk.Frame(sidebar, bg=BORDER_COLOR, height=1).pack(fill=tk.X, padx=8, pady=(12, 4))
        tk.Label(sidebar, text="LEGENDA WARNA:", bg=BG_PANEL, fg=TEXT_DIM,
                 font=("Courier", 8, "bold")).pack(padx=10, anchor="w")
        for name, col in [("Request-Response", ACCENT_BLUE), ("Publish-Subscribe", ACCENT_GREEN),
                           ("Message Passing", ACCENT_AMBER), ("RPC", ACCENT_PURPLE)]:
            f = tk.Frame(sidebar, bg=BG_PANEL)
            f.pack(fill=tk.X, padx=10, pady=1)
            tk.Label(f, text="●", bg=BG_PANEL, fg=col, font=("Courier", 10)).pack(side=tk.LEFT)
            tk.Label(f, text=f" {name}", bg=BG_PANEL, fg=TEXT_DIM, font=("Courier", 8)).pack(side=tk.LEFT)

    def _build_param_widgets(self):
        for w in self.param_frame.winfo_children():
            w.destroy()
        model = self.model_var.get()

        def lbl(text):
            tk.Label(self.param_frame, text=text, bg=BG_PANEL,
                     fg=TEXT_DIM, font=("Courier", 8), anchor="w").pack(fill=tk.X, pady=(4, 1))

        def entry(var, default):
            var.set(default)
            tk.Entry(self.param_frame, textvariable=var, bg=BG_DARK, fg=TEXT_MAIN,
                     font=("Courier", 9), insertbackground=TEXT_MAIN,
                     relief="flat", bd=4).pack(fill=tk.X, pady=(0, 4))

        if model == "Request-Response":
            self.v_client = tk.StringVar(); self.v_req = tk.StringVar()
            lbl("Client ID:");    entry(self.v_client, "C1")
            lbl("Data Request:"); entry(self.v_req, "get_data_from_db")

        elif model == "Publish-Subscribe":
            self.v_topic = tk.StringVar(); self.v_pub = tk.StringVar(); self.v_nsubs = tk.IntVar()
            lbl("Topik:");          entry(self.v_topic, "order.created")
            lbl("Publisher ID:");   entry(self.v_pub, "OrderService")
            lbl("Jumlah Subscriber (1-5):")
            self.v_nsubs.set(3)
            tk.Scale(self.param_frame, variable=self.v_nsubs, from_=1, to=5,
                     orient=tk.HORIZONTAL, bg=BG_PANEL, fg=TEXT_MAIN, troughcolor=BG_DARK,
                     highlightthickness=0, font=("Courier", 8),
                     activebackground=ACCENT_GREEN).pack(fill=tk.X, pady=(0, 4))

        elif model == "Message Passing":
            self.v_nodes = tk.StringVar(); self.v_chain_mode = tk.BooleanVar(value=True)
            lbl("Node (pisahkan koma):"); entry(self.v_nodes, "NodeA,NodeB,NodeC,NodeD")
            lbl("Mode Pengiriman:")
            f = tk.Frame(self.param_frame, bg=BG_PANEL)
            f.pack(fill=tk.X)
            for txt, val in [("Chain (Berantai)", True), ("Broadcast (Serentak)", False)]:
                tk.Radiobutton(f, text=txt, variable=self.v_chain_mode, value=val,
                               bg=BG_PANEL, fg=TEXT_MAIN, selectcolor=BG_DARK,
                               font=("Courier", 8)).pack(anchor="w")

        elif model == "RPC":
            self.v_rpc_client = tk.StringVar(); self.v_procedure = tk.StringVar(); self.v_args = tk.StringVar()
            lbl("Client ID:"); entry(self.v_rpc_client, "App-1")
            lbl("Nama Prosedur:")
            self.v_procedure.set("calculate_sum")
            ttk.Combobox(self.param_frame, textvariable=self.v_procedure, state="readonly",
                         values=["calculate_sum","get_user_info","process_data","check_inventory"],
                         font=("Courier", 9)).pack(fill=tk.X, pady=(0, 4))
            lbl("Argumen:"); entry(self.v_args, "10,20,30")

    def _build_center(self, parent):
        center = tk.Frame(parent, bg=BG_DARK)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas_frame = tk.Frame(center, bg=BG_PANEL,
                                 highlightthickness=1, highlightbackground=BORDER_COLOR)
        canvas_frame.pack(fill=tk.X, pady=(6, 4))
        tk.Label(canvas_frame, text="🗺  DIAGRAM ARSITEKTUR SISTEM",
                 bg=BG_PANEL, fg=TEXT_MAIN, font=("Courier", 9, "bold"), pady=6).pack(anchor="w", padx=10)
        self.canvas = ArchitectureCanvas(canvas_frame, height=200)
        self.canvas.pack(fill=tk.X, padx=8, pady=(0, 8))

        log_frame = tk.Frame(center, bg=BG_PANEL,
                              highlightthickness=1, highlightbackground=BORDER_COLOR)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))
        tk.Label(log_frame, text="📋  LOG KOMUNIKASI",
                 bg=BG_PANEL, fg=TEXT_MAIN, font=("Courier", 9, "bold"), pady=6).pack(anchor="w", padx=10)

        self.log_box = scrolledtext.ScrolledText(
            log_frame, bg=BG_DARK, fg=TEXT_MAIN, font=("Courier", 9),
            insertbackground=TEXT_MAIN, selectbackground="#264f78",
            relief="flat", wrap=tk.WORD, state=tk.DISABLED, height=12,
        )
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        for tag, col in [("blue", ACCENT_BLUE), ("green", ACCENT_GREEN), ("amber", ACCENT_AMBER),
                         ("purple", ACCENT_PURPLE), ("dim", TEXT_DIM),
                         ("success", TEXT_SUCCESS), ("error", TEXT_ERROR), ("main", TEXT_MAIN)]:
            self.log_box.tag_configure(tag, foreground=col)

        self.metrics = MetricsPanel(center)
        self.metrics.pack(fill=tk.BOTH, expand=False, pady=(0, 4))
        self.after(200, lambda: self.canvas.draw_model(self.model_var.get()))

    # --- Event handlers ---
    def _on_model_change(self, event=None):
        self._build_param_widgets()
        self.canvas.draw_model(self.model_var.get())

    def _run_simulation(self):
        model = self.model_var.get()
        self.canvas.draw_model(model)
        try:
            if model == "Request-Response":
                self.backend.run_request_response(
                    client_id    = self.v_client.get() or "C1",
                    request_data = self.v_req.get()    or "get_data",
                )
            elif model == "Publish-Subscribe":
                self.backend.run_publish_subscribe(
                    topic           = self.v_topic.get() or "events.update",
                    publisher       = self.v_pub.get()   or "Publisher",
                    num_subscribers = max(1, min(5, self.v_nsubs.get())),
                )
            elif model == "Message Passing":
                nodes = [n.strip() for n in (self.v_nodes.get() or "NodeA,NodeB,NodeC").split(",") if n.strip()]
                if len(nodes) < 2:
                    messagebox.showerror("Input Error", "Minimal 2 node diperlukan!")
                    return
                self.backend.run_message_passing(nodes=nodes, chain_mode=self.v_chain_mode.get())
            elif model == "RPC":
                self.backend.run_rpc(
                    client_id = self.v_rpc_client.get() or "App-1",
                    procedure = self.v_procedure.get()  or "calculate_sum",
                    args      = self.v_args.get()       or "1,2,3",
                )
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _clear_log(self):
        self.log_box.config(state=tk.NORMAL)
        self.log_box.delete("1.0", tk.END)
        self.log_box.config(state=tk.DISABLED)

    # --- Thread-safe log & callbacks ---
    def _enqueue_log(self, message: str, color: str = TEXT_MAIN):
        self._log_queue.put((message, color))

    def _poll_log_queue(self):
        try:
            while True:
                msg, color = self._log_queue.get_nowait()
                self._write_log(msg, color)
        except queue.Empty:
            pass
        self.after(50, self._poll_log_queue)

    def _write_log(self, message: str, color: str):
        tag_map = {
            ACCENT_BLUE: "blue", ACCENT_GREEN: "green", ACCENT_AMBER: "amber",
            ACCENT_PURPLE: "purple", TEXT_DIM: "dim", TEXT_SUCCESS: "success", TEXT_ERROR: "error",
        }
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, message + "\n", tag_map.get(color, "main"))
        self.log_box.see(tk.END)
        self.log_box.config(state=tk.DISABLED)

    def _on_metrics_update(self, model: str, data: dict):
        self.after(0, lambda: self.metrics.update_metrics(model, data))

    def _enqueue_flow(self, src: str, dst: str, color: str):
        self.after(0, lambda: self.canvas.animate_flow(src, dst, color))


# --- Entry Point ---

if __name__ == "__main__":
    app = DistributedSimApp()

    for delay, msg in [
        (500, "╔══════════════════════════════════════════════════════╗"),
        (550, "║  Selamat datang di Simulasi Sistem Terdistribusi!   ║"),
        (600, "║  Pilih model komunikasi di sidebar kiri, atur       ║"),
        (650, "║  parameter, lalu tekan [JALANKAN SIMULASI].         ║"),
        (700, "╚══════════════════════════════════════════════════════╝\n"),
    ]:
        app.after(delay, lambda m=msg: app._write_log(m, ACCENT_BLUE))
    app.after(750, lambda: app._write_log(
        "  Model tersedia: Request-Response | Pub-Sub | Message Passing | RPC\n", TEXT_DIM))

    app.mainloop()