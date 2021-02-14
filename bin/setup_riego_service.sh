#!/bin/sh


sudo bash -c "cat > /lib/systemd/system/riego.service" <<'EOT'
[Unit]
Description=Riego Rain-System
After=mnt-usb1.mount mosquitto.service memcached.service
StartLimitIntervalSec=500
StartLimitBurst=5

[Service]
Environment="PYTHONUNBUFFERED=1"
Type=simple
User=riego
WorkingDirectory=/mnt/usb1/riego
ExecStart=/mnt/usb1/riego/.venv/bin/riego
Restart=always
RestartSec=3s

[Install]
WantedBy=multi-user.target
EOT

systemctl daemon-reload
systemctl enable riego
systemctl restart riego
