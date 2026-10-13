#!/usr/bin/env bash
# Install the display as a boot service.   bash ~/np/install_service.sh
set -e

USER_NAME="$(whoami)"
SERVICE=/etc/systemd/system/nowplaying.service

if [ ! -x "$HOME/np/bin/python" ]; then
  echo "Can't find $HOME/np/bin/python -- is the venv there?"; exit 1
fi
if [ ! -f "$HOME/nowplaying.py" ]; then
  echo "Can't find $HOME/nowplaying.py"; exit 1
fi

echo "Installing service for user '$USER_NAME'..."
sudo sed -e "s|^User=.*|User=$USER_NAME|" \
         -e "s|^Group=.*|Group=$USER_NAME|" \
         -e "s|/home/andrew|$HOME|g" \
         "$HOME/np/nowplaying.service" | sudo tee "$SERVICE" >/dev/null

sudo systemctl daemon-reload
sudo systemctl enable nowplaying.service
sudo systemctl restart nowplaying.service
sleep 3
sudo systemctl --no-pager status nowplaying.service || true

echo
echo "Useful from now on:"
echo "  sudo systemctl stop nowplaying      # stop it (do this before running by hand)"
echo "  sudo systemctl start nowplaying"
echo "  sudo systemctl restart nowplaying   # after copying a new nowplaying.py"
echo "  sudo systemctl disable nowplaying   # stop it starting at boot"
echo "  journalctl -u nowplaying -f         # watch its output live"
