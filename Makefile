SHELL     := /bin/bash
REGISTRY  := ghcr.io/venom-algorithm/venom_vnv
CONTAINER := venom_sim
ROS_WS    := /ros_ws

.PHONY: help submodules build up down shell colcon rosdep \
        gazebo rviz2 ci-build clean push

help:
	@echo "Venom VNV Docker（仿真开发）"
	@echo ""
	@echo "  make submodules   初始化所有 git submodule"
	@echo "  make build        构建 sim 镜像（首次约 10-15 分钟）"
	@echo "  make up           启动 sim 容器（后台）"
	@echo "  make shell        进入容器 zsh"
	@echo "  make colcon       容器内执行 colcon build"
	@echo "  make rosdep       容器内执行 rosdep install"
	@echo "  make gazebo       容器内启动 Gazebo 仿真"
	@echo "  make rviz2        容器内启动 RViz2"
	@echo "  make ci-build     本地模拟 CI 无头构建"
	@echo "  make clean        删除容器 + named volumes（构建缓存）"
	@echo "  make push         推送镜像到 ghcr.io"

submodules:
	git submodule sync --recursive
	git submodule update --init --recursive

build:
	docker build \
		--file docker/Dockerfile.sim \
		--tag $(REGISTRY)/sim:latest \
		.

up:
	docker compose up -d sim

down:
	docker compose down

shell:
	docker exec -it $(CONTAINER) zsh

colcon:
	docker exec -it $(CONTAINER) bash -c "\
		source /opt/ros/humble/setup.bash && \
		cd $(ROS_WS) && \
		colcon build \
			--symlink-install \
			--cmake-args \
				-DCMAKE_BUILD_TYPE=Release \
				-DROS_EDITION=ROS2 \
				-DHUMBLE_ROS=humble \
			--event-handlers console_direct+"

rosdep:
	docker exec -it $(CONTAINER) bash -c "\
		source /opt/ros/humble/setup.bash && \
		cd $(ROS_WS) && \
		rosdep install -r --from-paths src --ignore-src --rosdistro humble -y"

gazebo:
	docker exec -it $(CONTAINER) bash -c "\
		source /opt/ros/humble/setup.bash && \
		source $(ROS_WS)/install/setup.bash && \
		ros2 launch rm_nav_bringup bringup_sim.launch.py"

rviz2:
	docker exec -it $(CONTAINER) bash -c "\
		source /opt/ros/humble/setup.bash && \
		source $(ROS_WS)/install/setup.bash && \
		rviz2"

ci-build:
	mkdir -p .ci_build/build .ci_build/install .ci_build/log
	docker run --rm \
		--volume "$(PWD):/ros_ws/src/venom_vnv:rw" \
		--volume "$(PWD)/.ci_build/build:/ros_ws/build:rw" \
		--volume "$(PWD)/.ci_build/install:/ros_ws/install:rw" \
		--volume "$(PWD)/.ci_build/log:/ros_ws/log:rw" \
		--env COLCON_WORKERS=2 \
		--env MAKE_JOBS=2 \
		$(REGISTRY)/sim:latest \
		bash /ros_ws/src/venom_vnv/scripts/ci-colcon-build.sh

clean:
	docker compose down -v
	rm -rf .ci_build/

push:
	docker push $(REGISTRY)/sim:latest
