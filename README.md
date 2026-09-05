# Capture-Condense-Cache (3C)

> **Open-Source, Air-Gapped Wearable Audio Logger & Offline AI Ingestion Pipeline**

A privacy-first, zero-cloud personal audio recording system designed to autonomously capture speech at the hardware edge and transcribe/structure it locally on a host computer without subscriptions, cloud APIs, or wireless data leaks.

---

## Pillar 1: Capture

mkdir build && cd build
cmake -DPICO_BOARD=pico2_w ..
make
ls /dev/cu.usb*
screen /dev/cu.usbmodemXXXXXX 115200

## License

MIT
