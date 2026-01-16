#include "my_best_controller/lab2_source.h"
#include <sstream>
#include "std_msgs/String.h"

SimpleController::SimpleController(std::string topic)
{
	std::string cmd, pose;
	cmd = topic + "/cmd_vel";
	pose = topic + "/pose";
	cmd_vel_pub = n.advertise<geometry_msgs::Twist>(cmd, 1);
	time_pub = n.advertise<std_msgs::String>("/result_368876", 1);
	pose_sub = n.subscribe(pose, 30, &SimpleController::pose_callback, this);
	target_sub = nullptr;
	target_x = target_y = x = y = 0.0;
}

SimpleController::SimpleController(const SimpleController & SimC)
{
	cmd_vel_pub = SimC.cmd_vel_pub;
	time_pub = SimC.time_pub;
	pose_sub = SimC.pose_sub;
	target_sub = new ros::Subscriber (*SimC.target_sub);
	target_x = SimC.target_x;
	target_y = SimC.target_y;
	x = SimC.x;
	y = SimC.y;
}

SimpleController::~SimpleController()
{
	delete target_sub;
}

void SimpleController::pose_callback(const turtlesim::Pose_<std::allocator<void>> msg)
{
	/*
	std::stringstream ss;
	ss << "current pose: " << msg.x << ' ' <<  msg.y;
	ROS_INFO("%s", ss.str().c_str());
	*/
	update_control(msg.x, msg.y);
}

void SimpleController::target_callback(const turtlesim::Pose_<std::allocator<void>> msg)
{
	/*
	std::stringstream ss;
        ss << "target updated with: " << msg.x << ' ' << msg.y;
        ROS_INFO("%s", ss.str().c_str());
	*/
	target_x = msg.x;
	target_y = msg.y;
}

void SimpleController::update_control(const double& new_x, const double& new_y)
{
    x = new_x;
    y = new_y;
}

void SimpleController::subscribe_on_turtle(const std::string topic)
{
	std::string turtle = topic + "/pose";
	*target_sub = n.subscribe(turtle, 1, &SimpleController::target_callback, this);
}

void SimpleController::go(const double route[][2], int size)
{
	ros::Time begin = ros::Time::now();
	geometry_msgs::Twist msg;
	ros::Rate rate(1);
	double diff_x, diff_y;
	for (int i = 0; i < size; ++i)
	{
		target_x = route[i][0];
		target_y = route[i][1];
		while (ros::ok())
		{
			ros::spinOnce();
			diff_x = target_x - x;
			diff_y = target_y - y;
			if (diff_x != 0.0 || diff_y != 0.0)
			{
				msg.linear.x = diff_x;
                        	msg.linear.y = diff_y;
				cmd_vel_pub.publish(msg);
				rate.sleep();
			}
			else
			{
				std::stringstream ss;
        			ss << "Point (" << target_x << ',' <<  target_y << ") acheived.";
			        ROS_INFO("%s", ss.str().c_str());
				break;
			}
		}
	}
	ros::Time end = ros::Time::now();
	ros::Duration result = end - begin;
	while (ros::ok())
		send_time(result);
}

void SimpleController::start_tracking(std::string topic)
{
	delete [] target_sub;
	std::string pose = topic + "/pose";
	target_sub = new ros::Subscriber (n.subscribe(pose, 1, &SimpleController::target_callback, this));
	geometry_msgs::Twist msg;
        ros::Rate rate(50);
        double diff_x, diff_y;
	while (ros::ok())
	{
		ros::spinOnce();
		diff_x = target_x - x;
		diff_y = target_y - y;
		if (diff_x != 0.0 || diff_y != 0.0)
		{
			if (diff_x < 0.000001 && diff_y < 0.000001)
			{
				msg.linear.x = diff_x;
                       		msg.linear.y = diff_y;
				cmd_vel_pub.publish(msg);
			}
			else
			{
                                msg.linear.x = 1.5 * diff_x;
                                msg.linear.y = 1.5 * diff_y;
                                cmd_vel_pub.publish(msg);
			}
		}
		rate.sleep();
	}
}

void SimpleController::send_time(const ros::Duration& time) const
{
	std_msgs::String msg;
	std::stringstream ss;
	ss << int(time.toSec()) / 60 << " min and "
		<< int(time.toSec()) % 60 << " sec";
	msg.data = ss.str();
	time_pub.publish(msg);
}
