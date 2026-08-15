import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node


def generate_launch_description():

    package_name = 'rccar_lab'

    # Robot State Publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory(package_name),
                'launch',
                'rsp.launch.py'
            )
        ),
        launch_arguments={
            'use_sim_time': 'true',
            'use_ros2_control': 'true'
        }.items()
    )

    # Gazebo Sim launch
    gazebo_pkg_name = 'ros_gz_sim'

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory(gazebo_pkg_name),
                'launch',
                'gz_sim.launch.py'
            )
        ),
        launch_arguments={
            'gz_args': '-r -s ' + os.path.join(
                get_package_share_directory(package_name),
                'config',
                'worlds',
                'more_objects.sdf'
            )
#             'gz_args': '-r empty.sdf'
        }.items()
    )


    # set resource path to fix error where it can't find meshes
    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.path.join(
            os.path.dirname(
                get_package_share_directory(package_name)
            )
        )
    )

    # Make Gazebo bridge
    gazebo_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'
        ],
        output='screen'
    )

    # Spawn robot into Gazebo
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'my_bot'
        ],
        output='screen'
    )

    # Delay spawners to ensure Gazebo + clock bridge are ready
    diff_drive_spawner = TimerAction(
        period=3.0,
        actions=[Node(
            package="controller_manager",
            executable="spawner",
            arguments=["diff_cont"],
            parameters=[{"use_sim_time": True}],
        )]
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"],
        parameters=[{"use_sim_time": True}],
    )

    # RViz2 Node
    rviz_config = os.path.join(
        get_package_share_directory(package_name),
        'config',
        'rviz',
        'lidar.rviz'
    )
    

    rviz = TimerAction(
        period=2.0,
        actions=[
            Node(
                package='rviz2',
                executable='rviz2',
                arguments=['-d', rviz_config],
                parameters=[{'use_sim_time': True}],
                output='screen'
            )
        ]
    )


    # Launch everything
    return LaunchDescription([
        gz_resource_path,
        rsp,
        gazebo,
        spawn_entity,
        gazebo_bridge,
        diff_drive_spawner,
        joint_broad_spawner,
        rviz
    ])


### control robot's movement in Gazebo / RViz
# ros2 run teleop_twist_keyboard teleop_twist_keyboard   --ros-args -r /cmd_vel:=/diff_cont/cmd_vel   -p stamped:=true

### SLAM stuff
# ros2 launch slam_toolbox online_async_launch.py params_file:=./src/rccar_lab/config/mapper_params_online_async.yaml use_sim_time:=truesudo

### move the turtle
# ros2 run teleop_twist_keyboard teleop_twist_keyboard   --ros-args -r /cmd_vel:=/turtle1/cmd_vel

### publish a twist stamped message to gazebo
#ros2 topic pub -r 10 /diff_cont/cmd_vel geometry_msgs/msg/TwistStamped \
#"{header: {frame_id: ''}, twist: {linear: {x: 0.0}, angular: {z: 1.0}}}"