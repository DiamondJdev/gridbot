FROM ros:jazzy-ros-base

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip python3-pytest ros-dev-tools
WORKDIR /workspace
COPY core /workspace/core
RUN python3 -m pip install --no-cache-dir --break-system-packages /workspace/core
COPY ros/src /workspace/src
RUN rosdep update --rosdistro jazzy && \
    rosdep install --from-paths src --ignore-src --rosdistro jazzy -y && \
    rm -rf /var/lib/apt/lists/*
RUN source /opt/ros/jazzy/setup.bash && colcon build

ENTRYPOINT ["/bin/bash", "-c", "source /opt/ros/jazzy/setup.bash && source /workspace/install/local_setup.bash && exec \"$@\"", "gridbot-ros"]
CMD ["ros2", "pkg", "list"]
