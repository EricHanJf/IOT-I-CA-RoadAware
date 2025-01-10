"use strict";

document.addEventListener("DOMContentLoaded", function () {
  var ledOnButton = document.getElementById("ledOnButton");
  var ledOffButton = document.getElementById("ledOffButton");
  var distanceOnButton = document.getElementById("distanceOnButton");
  var distanceOffButton = document.getElementById("distanceOffButton");
  var statusTextLED = document.getElementById("status-LED");
  var statusTextDistance = document.getElementById("status-distance");
  var distanceDisplay = document.getElementById("distance_id");
  var pubnub;
  var channelName = "RoadEasy";

  var setupPubNub = function setupPubNub() {
    pubnub = new PubNub({
      publishKey: "pub-c-5cba57b8-c321-4990-b00d-f0e48fcfaf18",
      subscribeKey: "sub-c-e90a4639-d5af-4167-9877-bac8afdf4d65",
      userId: "RoadEasy"
    }); // Subscribe to the channel

    pubnub.subscribe({
      channels: [channelName]
    }); // Set up listeners

    pubnub.addListener({
      message: handlePubNubMessage,
      // Call handlePubNubMessage when a message is received
      status: function status(statusEvent) {
        console.log("PubNub status:", statusEvent);
      }
    });
  }; // Handle incoming PubNub messages


  var handlePubNubMessage = function handlePubNubMessage(event) {
    var channel = event.channel;
    var message = event.message;

    if (channel === channelName && message.distance) {
      // If a message with distance is received, update the display
      updateDistanceDisplay(message.distance);
    } else if (message.command) {
      // Handle other commands like LED on/off
      handleMessage(message);
    } else {
      console.warn("Received message from unknown channel:", channel);
    }
  }; // Function to update the distance display on the page


  var updateDistanceDisplay = function updateDistanceDisplay(distance) {
    console.log("Received distance:", distance);
    var distanceValue = parseFloat(distance);

    if (!isNaN(distanceValue)) {
      // Update the displayed distance in the HTML element
      distanceDisplay.textContent = "".concat(distanceValue.toFixed(2), " cm");
    } else {
      console.warn("Invalid distance value:", distance);
    }
  }; // Handle other commands like LED on/off


  var handleMessage = function handleMessage(message) {
    console.log("Received Message:", message);

    if (message.command === "led on") {
      updateStatus(statusTextLED, "LED is ON");
    } else if (message.command === "led off") {
      updateStatus(statusTextLED, "LED is OFF");
    } else if (message.command === "distance on") {
      updateStatus(statusTextDistance, "Monitoring is ON");
    } else if (message.command === "distance off") {
      updateStatus(statusTextDistance, "Monitoring is OFF");
    } else {
      console.warn("Unknown command:", message.command);
    }

    if (message.distance !== undefined) {
      document.getElementById("distance_id").textContent = "".concat(message.distance.toFixed(2), " cm");
      storeDistanceData(message.distance);
    }

    console.log("Received message:", message);

    var storeDistanceData = function storeDistanceData(distance) {
      fetch("https://www.sd3siot.online/api/store_distance_data", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          distance: distance
        })
      }).then(function (response) {
        if (!response.ok) {
          throw new Error("HTTP error! status: ".concat(response.status));
        }

        return response.json();
      }).then(function (data) {
        return console.log("Distance data stored:", data);
      })["catch"](function (error) {
        return console.error("Error storing distance data:", error);
      });
    };
  }; // Send LED command to PubNub


  var sendLEDCommand = function sendLEDCommand(command) {
    pubnub.publish({
      channel: channelName,
      message: {
        command: command
      }
    }, function (status, response) {
      if (status.error) {
        console.error("PubNub publish error:", status);
      } else {
        console.log("Command sent successfully:", command);
      }
    });
  }; // Update LED status text
  // const updateLEDStatus = (status) => {
  //     statusText.textContent = `Status: ${status}`;
  // };


  var updateStatus = function updateStatus(statusElement, status) {
    statusElement.textContent = "Status: ".concat(status);
  }; // Set up event listeners for buttons


  ledOnButton.addEventListener("click", function () {
    sendLEDCommand("led on");
  });
  ledOffButton.addEventListener("click", function () {
    sendLEDCommand("led off");
  });
  distanceOnButton.addEventListener("click", function () {
    sendLEDCommand("distance on");
  });
  distanceOffButton.addEventListener("click", function () {
    sendLEDCommand("distance off");
  }); // Initialize PubNub

  setupPubNub();
});