#ifndef CONTROLLER
#define CONTROLLER

#include "ros/ros.h"
#include "geometry_msgs/Twist.h"
#include "turtlesim/Pose.h"
#include <string>

class SimpleController
{
private: 
	ros::NodeHandle n;
	ros::Publisher cmd_vel_pub;
	ros::Publisher time_pub;
	ros::Subscriber pose_sub;
	ros::Subscriber* target_sub;
	double target_x;
       	double target_y;
       	double x;
       	double y;	

public:
	SimpleController(std::string topic = "/turtle1");
	SimpleController(const SimpleController & SimC);
	~SimpleController();
	void pose_callback(const turtlesim::Pose_<std::allocator<void>> msg);
	void target_callback(const turtlesim::Pose_<std::allocator<void>> msg);
	void update_control(const double& new_x, const double& new_y);
	void subscribe_on_turtle(const std::string topic);
	void go(const double route[][2], int size);
	void start_tracking(std::string topic);
	void send_time(const ros::Duration& time) const;
};

#endif
