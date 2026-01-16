#include <cstdlib>
#include <ctime>
#include "ros/ros.h"
#include "std_msgs/Int16.h"

int main(int argc, char **argv)
{
	srand(time(0));
        ros::init(argc, argv, "node3");
        ros::NodeHandle n;
        ros::Publisher num_gen_pub = n.advertise<std_msgs::Int16>("connection_3",30);
        std_msgs::Int16 number;
	number.data = rand() % 1000;
	ros::Rate loop_rate(1);
        while (ros::ok())
        {
                num_gen_pub.publish(number);
                ros::spinOnce();
                loop_rate.sleep();
        }

        return 0;
}      
