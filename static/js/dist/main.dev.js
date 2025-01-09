"use strict";

document.addEventListener("DOMContentLoaded", function () {
  var ledOnButton = document.getElementById("ledOnButton");
  var ledOffButton = document.getElementById("ledOffButton");
  var distanceOnButton = document.getElementById("distanceOnButton");
  var distanceOffButton = document.getElementById("distanceOffButton");
  var statusText = document.getElementById("status");
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
      status: function status(statusEvent) {
        console.log("PubNub status:", statusEvent);
      }
    });
  }; // Handle incoming PubNub messages


  var handlePubNubMessage = function handlePubNubMessage(event) {
    var channel = event.channel;
    var message = event.message;

    if (channel === channelName && message.command) {
      handleMessage(message);
    } else {
      console.warn("Received message from unknown channel:", channel);
    }
  };

  var handleMessage = function handleMessage(message) {
    console.log("Received Message:", message);

    if (message.command === "led on") {
      updateLEDStatus("LED is ON");
    } else if (message.command === "led off") {
      updateLEDStatus("LED is OFF");
    } else if (message.command === "distance on") {
      updateLEDStatus("Distance is ON");
    } else if (message.command === "distance off") {
      updateLEDStatus("Distance is OFF");
    } else {
      console.warn("Unknown command:", message.command);
    }
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


  var updateLEDStatus = function updateLEDStatus(status) {
    statusText.textContent = "Status: ".concat(status);
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