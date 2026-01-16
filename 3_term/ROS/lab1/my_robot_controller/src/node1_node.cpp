#include "ros/ros.h"
#include "std_msgs/Int16.h"

static std_msgs::Int16 num1;
static std_msgs::Int16 num2;

void Callback_1(const boost::shared_ptr<const std_msgs::Int16_<std::allocator<void>>> number)
{
	num1.data = number->data;
}

void Callback_2(const boost::shared_ptr<const std_msgs::Int16_<std::allocator<void>>> number)
{
	num2.data = number->data;
}

int main(int argc, char**argv)
{
	std_msgs::Int16 diff;
	ros::init(argc, argv, "node1");
	ros::NodeHandle n;
	ros::Subscriber num_1_sub = n.subscribe<std_msgs::Int16>("connection_2", 30, Callback_1);
	ros::Subscriber num_2_sub = n.subscribe<std_msgs::Int16>("connection_3", 30, Callback_2);
	ros::Publisher num_diff = n.advertise<std_msgs::Int16>("result_368876", 30);
	ros::Rate loop_rate(1);
	while (ros::ok())
	{
		diff.data = num1.data - num2.data;
		num_diff.publish(diff);
		ros::spinOnce();
		loop_rate.sleep();
	}

	return 0;
}
