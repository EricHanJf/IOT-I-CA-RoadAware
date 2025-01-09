document.addEventListener("DOMContentLoaded", () => {
    const ledOnButton = document.getElementById("ledOnButton");
    const ledOffButton = document.getElementById("ledOffButton");
    const distanceOnButton = document.getElementById("distanceOnButton");
    const distanceOffButton = document.getElementById("distanceOffButton");
    const statusText = document.getElementById("status");

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
            message: handlePubNubMessage,
            status: (statusEvent) => {
                console.log("PubNub status:", statusEvent);
            },
        });
    };

    // Handle incoming PubNub messages
    const handlePubNubMessage = (event) => {
        const channel = event.channel;
        const message = event.message;

        if (channel === channelName && message.command) {
            handleMessage(message);
        } else {
            console.warn("Received message from unknown channel:", channel);
        }
    };

    const handleMessage = (message) => {
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
    const updateLEDStatus = (status) => {
        statusText.textContent = `Status: ${status}`;
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
    })

    // Initialize PubNub
    setupPubNub();
});
