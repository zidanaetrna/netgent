"""Pre-packaged laboratory assignments and topology presets for NetGent."""

from typing import Any, Dict

LAB_PRESETS: Dict[str, Dict[str, Any]] = {
    "Praktikum 2: LAN Switch (3 PCs)": {
        "recipe_file": "topologies/praktikum2_lan_switch.yaml",
        "project_name": "lab_praktikum_2",
        "prompt": (
            "M. PRAKTIKUM 2 — Membangun LAN Menggunakan Switch\n"
            "Gunakan Cisco Packet Tracer.\n"
            "Tugas:\n"
            "Buat jaringan: PC1 — Switch — PC2 — PC3\n"
            "1. Hubungkan tiga PC ke switch 2960.\n"
            "2. Konfigurasikan alamat IP setiap PC (192.168.1.10, 192.168.1.20, 192.168.1.30 /24).\n"
            "3. Pastikan setiap PC berada pada jaringan yang sesuai.\n"
            "4. Lakukan pengujian komunikasi antar-PC menggunakan ping.\n"
            "5. Dokumentasikan konfigurasi dan hasil pengujian.\n\n"
            "Pertanyaan Teori:\n"
            "1. Mengapa PC membutuhkan NIC?\n"
            "2. Apa fungsi switch pada simulasi?\n"
            "3. Bagaimana switch menentukan port tujuan?\n"
            "4. Apa yang terjadi jika salah satu alamat IP dikonfigurasi salah?\n"
            "5. Apa yang terjadi jika kabel salah terhubung?"
        ),
        "academic_answers": (
            "### Jawaban Analisis Praktikum 2 — Membangun LAN Menggunakan Switch\n\n"
            "**1. Mengapa PC membutuhkan NIC (Network Interface Card)?**\n"
            "NIC adalah perangkat keras antarmuka fisik yang mengubah data digital dari sistem operasi PC "
            "menjadi sinyal listrik/cahaya yang dapat ditransmisikan melalui media kabel transmisi Ethernet. "
            "NIC juga menyediakan alamat fisik (MAC Address) unik global pada Layer 2 OSI.\n\n"
            "**2. Apa fungsi switch pada simulasi?**\n"
            "Switch bekerja pada Lapisan Data Link (Layer 2 OSI) dan berfungsi sebagai konsentrator sentral "
            "yang meneruskan frame antar-perangkat secara selektif (unicast) berdasarkan tabel MAC address, "
            "sehingga memecah domain tabrakan (collision domain) dan mencegah tabrakan transmisi.\n\n"
            "**3. Bagaimana switch menentukan port tujuan?**\n"
            "Switch membaca *Source MAC Address* dari frame yang masuk untuk mempelajari (*learning*) port asal "
            "dan mencatatnya ke dalam tabel CAM (Content Addressable Memory). Ketika frame hendak dikirimkan, "
            "switch memeriksa *Destination MAC Address* pada tabel CAM untuk meneruskannya langsung ke port tujuan.\n\n"
            "**4. Apa yang terjadi jika salah satu alamat IP dikonfigurasi salah?**\n"
            "Jika salah satu PC dikonfigurasi dengan subnet berbeda (misal 192.168.2.10/24), PC pengirim akan "
            "menganggap target berada di luar jaringan lokal dan mencoba mencari Default Gateway. Karena tidak ada "
            "router di jaringan ini, paket ARP gagal dan uji ping akan menghasilkan status *Request Timed Out*.\n\n"
            "**5. Apa yang terjadi jika kabel salah terhubung?**\n"
            "Jika menggunakan jenis kabel yang tidak sesuai atau port yang tidak aktif/salah port, status fisik "
            "link akan Down (indikator merah) atau auto-MDIX tidak bernegosiasi, menyebabkan komunikasi terputus total."
        ),
    },
    "Praktikum 3: Two Networks Router (2 Subnets)": {
        "recipe_file": "topologies/praktikum3_two_networks_router.yaml",
        "project_name": "lab_praktikum_3",
        "prompt": (
            "N. PRAKTIKUM 3 — Menghubungkan Dua Network Menggunakan Router\n"
            "Gunakan Cisco Packet Tracer.\n"
            "Buat dua jaringan:\n"
            "Network 1: 192.168.1.0/24 (Switch 1, PC1 192.168.1.10, PC2 192.168.1.20)\n"
            "Network 2: 192.168.2.0/24 (Switch 2, PC3 192.168.2.10, PC4 192.168.2.20)\n"
            "Tugas:\n"
            "1. Hubungkan perangkat dalam setiap jaringan menggunakan switch 2960.\n"
            "2. Hubungkan kedua jaringan menggunakan router Cisco 2911.\n"
            "3. Konfigurasikan interface router (Gig0/0: 192.168.1.1/24, Gig0/1: 192.168.2.1/24).\n"
            "4. Konfigurasikan IP address dan default gateway pada setiap PC.\n"
            "5. Lakukan pengujian komunikasi antarjaringan (PC1 -> PC3, PC2 -> PC4).\n\n"
            "Pertanyaan Teori:\n"
            "1. Mengapa dua network berbeda membutuhkan router?\n"
            "2. Apa fungsi default gateway?\n"
            "3. Apa fungsi switch dalam masing-masing network?\n"
            "4. Bagaimana router menentukan tujuan packet?\n"
            "5. Apa yang terjadi jika interface router tidak dikonfigurasi dengan benar?"
        ),
        "academic_answers": (
            "### Jawaban Analisis Praktikum 3 — Menghubungkan Dua Network Menggunakan Router\n\n"
            "**1. Mengapa dua network berbeda membutuhkan router?**\n"
            "Perangkat switch Layer 2 hanya dapat meneruskan paket dalam satu broadcast domain yang sama. "
            "Untuk menghubungkan dua subnet berlainan (192.168.1.0/24 dan 192.168.2.0/24), diperlukan perangkat "
            "Network Layer (Layer 3 OSI) yaitu Router yang mampu merutekan paket berdasarkan IP address logis.\n\n"
            "**2. Apa fungsi default gateway?**\n"
            "Default Gateway adalah alamat IP interface router pada subnet lokal yang menjadi pintu keluar (exit point) "
            "bagi host ketika mengirim paket ke tujuan di luar subnet lokalnya.\n\n"
            "**3. Apa fungsi switch dalam masing-masing network?**\n"
            "Switch bertindak sebagai konsentrator local access yang menghubungkan workstation dalam satu segmen LAN "
            "ke interface gateway router dengan kecepatan transfer tinggi dan tanpa tabrakan transmisi.\n\n"
            "**4. Bagaimana router menentukan tujuan packet?**\n"
            "Router memeriksa header IP pada paket, membaca *Destination IP Address*, lalu mencocokkannya dengan entri "
            "pada Tabel Perutean (*Routing Table*) menggunakan prinsip *longest prefix match* untuk menentukan outgoing interface.\n\n"
            "**5. Apa yang terjadi jika interface router tidak dikonfigurasi dengan benar?**\n"
            "Jika interface router lupa di-`no shutdown`, atau salah subnet mask/IP, interface akan berstatus *administratively down* "
            "atau routing table tidak memiliki entri rute langsung. Host pengirim akan menerima balasan *Destination Host Unreachable*."
        ),
    },
    "Simulasi 2: Lab Informatika": {
        "recipe_file": "topologies/lab_informatika.yaml",
        "project_name": "lab_informatika_run",
        "prompt": (
            "G. SIMULASI 2 Laboratorium Informatika\n"
            "Sebuah laboratorium memiliki:\n"
            "• 30 PC, 1 Server, 2 Printer, 2 Access Point, 1 Router, Koneksi Internet\n"
            "Tugas:\n"
            "1. Tentukan komponen hardware yang diperlukan.\n"
            "2. Tentukan jenis media transmisi yang digunakan.\n"
            "3. Tentukan posisi switch, router, dan access point.\n"
            "4. Konfigurasi addressing dan routing.\n"
            "5. Lakukan pengujian konektivitas."
        ),
        "academic_answers": (
            "### Rancangan & Analisis Simulasi 2 — Laboratorium Informatika\n\n"
            "**1. Komponen Hardware**:\n"
            "- 1x Router Cisco 2911 (Edge Gateway & NAT/Firewall)\n"
            "- 2x Switch Cisco Catalyst 2960 (24-Port) untuk Workstation & Server\n"
            "- 1x Server Farm (DHCP, DNS, File Server)\n"
            "- 2x Network Printer (FastEthernet)\n"
            "- 2x Wireless Access Point (Coverage ruang lab)\n\n"
            "**2. Media Transmisi**:\n"
            "- Kabel UTP Cat6 Straight-Through (PC/Server/AP ke Switch)\n"
            "- Kabel UTP Cat6 Crossover / Gigabit Uplink (Inter-switch trunking)\n"
            "- Sinyal Gelombang Radio 2.4/5 GHz untuk Wireless AP\n\n"
            "**3. Topologi & Posisi**:\n"
            "- Router di Core/Edge rack terhubung ke ISP.\n"
            "- Distribution switches di rak tengah lab menghubungkan workstation secara simetris."
        ),
    },
    "NEXORA Technologies (Enterprise 3-Tier)": {
        "recipe_file": "topologies/nexora_technologies.yaml",
        "project_name": "nexora_technologies_run",
        "prompt": (
            "NEXORA Technologies - 3-Floor Enterprise Campus Network Infrastructure\n"
            "Edge Router -> Core L3 Switch -> 3 Floor Access Switches (SW-01, SW-02, SW-03)\n"
            "VLAN Segmentation: VLAN 10 Management, VLAN 20 Employees, VLAN 30 Developers,\n"
            "VLAN 40 Guest, VLAN 50 Voice, VLAN 60 CCTV, VLAN 70 Servers, VLAN 80 Printers, VLAN 99 Native\n"
            "4 Servers: DNS (10.10.70.10), Git (10.10.70.20), Monitoring (10.10.70.30), Web (10.10.70.40)\n"
            "Inter-VLAN routing, Rapid-PVST+ STP Root, 802.1Q Trunks, PortFast, BPDU Guard, and NAT/PAT."
        ),
        "academic_answers": (
            "### Analisis & Desain Arsitektur Enterprise — NEXORA Technologies\n\n"
            "**1. Desain Hirarki 3-Tier Enterprise**:\n"
            "- **Edge/Core Layer**: Router Cisco 2911 terhubung ke ISP dengan NAT/PAT untuk proteksi IP internal, "
            "dan Core Switch Layer-3 (Catalyst 3560) menjalankan Inter-VLAN routing berkecepatan kawat (hardware wire-speed).\n"
            "- **Distribution/Access Layer**: 3x Switch Catalyst 2960 (SW-01, SW-02, SW-03) melayani workstation lantai 1, 2, dan 3 "
            "menggunakan link trunk 802.1Q dengan native VLAN 99.\n\n"
            "**2. Segmentasi VLAN & Subnetting**:\n"
            "- VLAN 10 (Management): 10.10.10.0/24 (Gateway: 10.10.10.1)\n"
            "- VLAN 20 (Employees): 10.10.20.0/23 (Gateway: 10.10.20.1)\n"
            "- VLAN 30 (Developers): 10.10.30.0/24 (Gateway: 10.10.30.1)\n"
            "- VLAN 40 (Guest): 10.10.40.0/23 (Gateway: 10.10.40.1)\n"
            "- VLAN 70 (Servers): 10.10.70.0/24 (Gateway: 10.10.70.1) — Server 01 s/d 04\n"
            "- VLAN 99 (Native/Blackhole): VLAN tidak terpakai dinonaktifkan untuk mencegah VLAN Hopping.\n\n"
            "**3. Redundansi & Spanning Tree (STP)**:\n"
            "- Menggunakan protokol Rapid-PVST+ (`spanning-tree mode rapid-pvst`).\n"
            "- Core L3 Switch dikonfigurasi sebagai STP Root Primary untuk seluruh VLAN (`spanning-tree vlan 1-99 root primary`).\n"
            "- Access ports diproteksi dengan `spanning-tree portfast` dan `spanning-tree bpduguard enable`.\n\n"
            "**4. Keamanan Akses & Isolasi**:\n"
            "- Guest VLAN hanya memiliki akses rute keluar ke Internet (tidak diizinkan menjangkau Server Farm atau Management VLAN).\n"
            "- Akses manajemen perangkat (SSH) dibatasi hanya dari Management VLAN 10."
        ),
    },
    "Perancangan Integratif Universitas (Enterprise Campus)": {
        "recipe_file": "topologies/universitas_integratif.yaml",
        "project_name": "universitas_integratif_run",
        "prompt": (
            "V. UJI KOMPETENSI 5 — PERANCANGAN INTEGRATIF KAMPUS UNIVERSITAS\n"
            "Arsitektur jaringan kampus 4 gedung, 10 laboratorium, data center server akademik, Wi-Fi, dan redundansi high-availability.\n"
            "1. Core L3 Switch redundan (Dual Core 3560) dengan Rapid-PVST+ dan HSRP/VRRP.\n"
            "2. Distribution switch di setiap gedung A-D menghubungkan laboratorium dan ruang dosen.\n"
            "3. Server Farm: Server Akademik (SIAKAD), Web/DNS, dan Database di VLAN 50.\n"
            "4. Segmentasi VLAN: VLAN 10 Mgmt, VLAN 20 Dosen, VLAN 30 Mahasiswa/Lab, VLAN 40 Wi-Fi, VLAN 50 Servers.\n"
            "5. Analisis SPOF, mitigasi fault tolerance, dan verifikasi konektivitas ICMP."
        ),
        "academic_answers": (
            "### Analisis & Desain Arsitektur Perancangan Integratif Kampus Universitas\n\n"
            "**1. Struktur Hirarki Enterprise 3-Tier**:\n"
            "- Core Layer: Dual Multilayer Switch (Core-01 & Core-02) terhubung inter-switch trunk berkecepatan tinggi dengan Rapid-PVST+ root primary/secondary.\n"
            "- Distribution Layer: Switch agregasi per gedung (A-D) mengisolasi broadcast domain dan mengelola trunking 802.1Q.\n"
            "- Access Layer: Melayani PC laboratorium (VLAN 30) dengan port security, PortFast, dan BPDU Guard.\n\n"
            "**2. Redundansi & Mitigasi SPOF**:\n"
            "- Dual-homed uplink dari tiap gedung ke kedua Core Switch.\n"
            "- HSRP virtual gateway mencegah single point of failure pada gateway default.\n"
            "- Server Farm terpusat di Data Center dengan pendingin presisi dan dual power supply."
        ),
    },
    "Partial Mesh 10 Router (Enterprise OSPF Backbone)": {
        "recipe_file": "topologies/partial_mesh_10routers.yaml",
        "project_name": "partial_mesh_10routers_run",
        "prompt": (
            "Perancangan Jaringan WAN 10 Router: Full Mesh vs Partial Mesh\n"
            "1. Analisis kebutuhan link Full Mesh: L = N(N-1)/2 = 45 link, 9 port/router.\n"
            "2. Implementasi Partial Mesh: 10 Router Cisco 2911 dengan 14-16 point-to-point links /30.\n"
            "3. Routing Dinamis: OSPF Area 0 konvergensi cepat dan load balancing multi-path.\n"
            "4. Redundansi & Toleransi Kerusakan: Ring luar redundan + cross-chord inner mesh.\n"
            "5. Endpoint: PC-HQ ke PC-CABANG uji keterjangkauan ujung-ke-ujung."
        ),
        "academic_answers": (
            "### Analisis Desain 10 Router Full Mesh vs Partial Mesh\n\n"
            "**1. Formula & Kebutuhan Link**:\n"
            "- Full Mesh 10 Router membutuhkan 45 link fisik dan 9 port per router (total 90 port).\n"
            "- Partial Mesh rancangan ini hanya membutuhkan 14-16 link fisik dan maksimal 3 port onboard (Gi0/0-Gi0/2), menghemat lebih dari 68% kabel dan perangkat.\n\n"
            "**2. Keunggulan Partial Mesh**:\n"
            "- Mengeliminasi SPOF dengan menyediakan 2-3 jalur alternatif di setiap node.\n"
            "- Menggunakan protokol routing OSPF Area 0 untuk failover otomatis sub-detik jika salah satu link putus.\n"
            "- Sepenuhnya kompatibel dengan interface bawaan router Cisco 2911 tanpa modul ekspansi mahal."
        ),
    },
    "Tugas Psikomotorik 3: Master Showcase (Bus, Star, Ring, Mesh, Hybrid)": {
        "recipe_file": "topologies/psikomotorik_master.yaml",
        "project_name": "psikomotorik_master_run",
        "prompt": (
            "3. Pertanyaan Psikomotorik Topologi Jaringan\n"
            "1. Topologi Bus: 5 Komputer + Backbone Hub Rantai + Titik Kritis Kegagalan.\n"
            "2. Topologi Star: 5 Komputer + 1 Switch Sentral 2960.\n"
            "3. Topologi Ring: 4 Node Ring Loop Tertutup + 4 Komputer.\n"
            "4. Topologi Mesh: 4 Router Cisco 2911 Full Mesh 6 Link + Jalur Alternatif Multi-Path.\n"
            "5. Topologi Hybrid: Penggabungan Star LAN (Pusat & Cabang) dan Mesh WAN."
        ),
        "academic_answers": (
            "### Analisis Master Showcase 5 Topologi Psikomotorik\n\n"
            "**1. No 1 - Topologi Bus (5 PC)**:\n"
            "- Backbone rantai 5 Hub dengan titik kritis di Hub 3. Jika link putus, jaringan terbelah dua.\n\n"
            "**2. No 2 - Topologi Star (5 PC)**:\n"
            "- Switch Catalyst 2960 sebagai konsentrator pusat. Kegagalan PC tidak mengganggu PC lain.\n\n"
            "**3. No 3 - Topologi Ring (4 PC)**:\n"
            "- 4 Node loop tertutup dengan transmisi token searah jarum jam.\n\n"
            "**4. No 4 - Topologi Mesh (4 Router)**:\n"
            "- 4 Router Full Mesh (6 link OSPF Area 0). Jalur utama R1-R3 didukung 2 jalur cadangan via R2 dan R4.\n\n"
            "**5. No 5 - Topologi Hybrid**:\n"
            "- Menggabungkan keandalan Mesh pada layer WAN dan efisiensi Star pada layer LAN lokal."
        ),
    },
}
