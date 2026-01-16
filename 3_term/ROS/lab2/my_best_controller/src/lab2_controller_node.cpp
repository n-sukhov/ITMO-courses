#include "my_best_controller/lab2_source.h"
#include "lab2_source.cpp"
#include "ros/ros.h"
#include <string>

int main(int argc, char** argv)
{
        double (*route)[2] = new double[3][2]
        {
                {4.0, 2.0},
                {7.0, 1.0},
                {5.0,4.0},
        };
        ros::init(argc, argv, "t");
	std::string ns = ros::this_node::getNamespace() + "/turtle1";
	SimpleController turtle(ns);
	if (ns == "/ns1_368876/turtle1")
		turtle.go(route, 3);
	else
		turtle.start_tracking("/ns1_368876/turtle1");
	ros::spin();
	delete [] route;
	return 0;
}

