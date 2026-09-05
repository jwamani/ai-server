# Infrastructure

This directory will contain Docker Compose definitions for the control-plane
services and a separately built, hardened sandbox image. The sandbox image must
never inherit API/worker secrets or mount the Docker socket.
