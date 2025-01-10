document.addEventListener("DOMContentLoaded", () => {
    const ledOnButton = document.getElementById("ledOnButton");
    const ledOffButton = document.getElementById("ledOffButton");
    const distanceOnButton = document.getElementById("distanceOnButton");
    const distanceOffButton = document.getElementById("distanceOffButton");
    const statusTextLED = document.getElementById("status-LED");
    const statusTextDistance = document.getElementById("status-distance");
    const distanceDisplay = document.getElementById("distance_id");

    let pubnub;
    const channelName = "RoadEasy";

    const setupPubNub = () => {
        pubnub = new PubNub({
            publishKey: "pub-c-5cba57b8-c321-4990-b00d-f0e48fcfaf18",
            subscribeKey: "sub-c-e90a4639-d5af-4167-9877-bac8afdf4d65",
            userId: "RoadEasy",
        });

        // Subscribe to the channel
        pubnub.subscribe({
            channels: [channelName],
        });

        // Set up listeners
        pubnub.addListener({
            message: handlePubNubMessage, // Call handlePubNubMessage when a message is received
            status: (statusEvent) => {
                console.log("PubNub status:", statusEvent);
            },
        });
    };

    // Handle incoming PubNub messages
    const handlePubNubMessage = (event) => {
        const channel = event.channel;
        const message = event.message;

        if (channel === channelName && message.distance) {
            // If a message with distance is received, update the display
            updateDistanceDisplay(message.distance);
        } else if (message.command) {
            // Handle other commands like LED on/off
            handleMessage(message);
        } else {
            console.warn("Received message from unknown channel:", channel);
        }
    };

    // Function to update the distance display on the page
    const updateDistanceDisplay = (distance) => {
        console.log("Received distance:", distance);
        const distanceValue = parseFloat(distance);
        if (!isNaN(distanceValue)) {
            // Update the displayed distance in the HTML element
            distanceDisplay.textContent = `${distanceValue.toFixed(2)} cm`;
        } else {
            console.warn("Invalid distance value:", distance);
        }
    };

    // Handle other commands like LED on/off
    const handleMessage = (message) => {
        console.log("Received Message:", message);

        if (message.command === "led on") {
            updateStatus(statusTextLED,"LED is ON");
        } else if (message.command === "led off") {
            updateStatus(statusTextLED,"LED is OFF");
        } else if (message.command === "distance on") {
            updateStatus(statusTextDistance,"Monitoring is ON");
        } else if (message.command === "distance off") {
            updateStatus(statusTextDistance,"Monitoring is OFF");
        } else {
            console.warn("Unknown command:", message.command);
        }

        if (message.distance !== undefined) {
            document.getElementById("distance_id").textContent = `${message.distance.toFixed(2)} cm`;
            storeDistanceData(message.distance);
          }

        console.log("Received message:", message);
        const storeDistanceData = (distance) => {
            fetch("https://www.sd3siot.online/api/store_distance_data", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ distance }),
            })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then((data) => console.log("Distance data stored:", data))
                .catch((error) => console.error("Error storing distance data:", error));
        };
        
    };

    // Send LED command to PubNub
    const sendLEDCommand = (command) => {
        pubnub.publish({
            channel: channelName,
            message: { command },
        }, (status, response) => {
            if (status.error) {
                console.error("PubNub publish error:", status);
            } else {
                console.log("Command sent successfully:", command);
            }
        });
    };

    // Update LED status text
    // const updateLEDStatus = (status) => {
    //     statusText.textContent = `Status: ${status}`;
    // };
    const updateStatus = (statusElement, status) => {
        statusElement.textContent = `Status: ${status}`;
    };
    // Set up event listeners for buttons
    ledOnButton.addEventListener("click", () => {
        sendLEDCommand("led on");
    });

    ledOffButton.addEventListener("click", () => {
        sendLEDCommand("led off");
    });

    distanceOnButton.addEventListener("click", () => {
        sendLEDCommand("distance on");
    });

    distanceOffButton.addEventListener("click", () => {
        sendLEDCommand("distance off");
    });

    // Initialize PubNub
    setupPubNub();
});
