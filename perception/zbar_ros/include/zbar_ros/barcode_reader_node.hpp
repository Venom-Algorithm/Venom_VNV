/**
*
*  \author     Paul Bovbel <pbovbel@clearpathrobotics.com>
*  \copyright  Copyright (c) 2014, Clearpath Robotics, Inc.
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*     * Redistributions of source code must retain the above copyright
*       notice, this list of conditions and the following disclaimer.
*     * Redistributions in binary form must reproduce the above copyright
*       notice, this list of conditions and the following disclaimer in the
*       documentation and/or other materials provided with the distribution.
*     * Neither the name of Clearpath Robotics, Inc. nor the
*       names of its contributors may be used to endorse or promote products
*       derived from this software without specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
* ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL CLEARPATH ROBOTICS, INC. BE LIABLE FOR ANY
* DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
* (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
* LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
* ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
* SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*
* Please send comments, questions, or patches to code@clearpathrobotics.com
*
*/
#ifndef ZBAR_ROS__BARCODE_READER_NODE_HPP_
#define ZBAR_ROS__BARCODE_READER_NODE_HPP_

#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "zbar_interfaces/msg/barcode_detection.hpp"
#include "zbar_interfaces/msg/barcode_detections.hpp"
#include <zbar.h>

namespace zbar_ros
{

class BarcodeReaderNode : public rclcpp::Node
{
public:
  BarcodeReaderNode();

private:
  using ImageMsg = sensor_msgs::msg::Image;
  using BarcodeDetectionMsg = zbar_interfaces::msg::BarcodeDetection;
  using BarcodeDetectionsMsg = zbar_interfaces::msg::BarcodeDetections;

  void imageCb(ImageMsg::ConstSharedPtr image);
  BarcodeDetectionMsg buildDetection(const zbar::Symbol & symbol) const;
  void publishDebugImage(
    const ImageMsg::ConstSharedPtr & image,
    const std::vector<BarcodeDetectionMsg> & detections);

  rclcpp::Subscription<ImageMsg>::SharedPtr image_sub_;
  rclcpp::Publisher<BarcodeDetectionsMsg>::SharedPtr detections_pub_;
  rclcpp::Publisher<ImageMsg>::SharedPtr debug_image_pub_;
  zbar::ImageScanner scanner_;
  bool publish_debug_image_{true};
  bool qrcode_only_{true};
};

}  // namespace zbar_ros

#endif  // ZBAR_ROS__BARCODE_READER_NODE_HPP_
