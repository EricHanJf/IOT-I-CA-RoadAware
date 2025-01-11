let pubnub;
let appChannel = "RoadEasy";
let ttl = 5;
user_Id = "{{ user_id }}";
function refreshToken()
{
    console.log("Get user token request");
    sendEvent('get_user_token');
    let refresh_time = (ttl-1)*60*1000;
    console.log(refresh_time);
    setTimeout('refreshToken()', refresh_time);
}

const setupPubNub = () => {
    pubnub = new PubNub({
        publishKey: "pub-c-5cba57b8-c321-4990-b00d-f0e48fcfaf18",
        subscribeKey: "sub-c-e90a4639-d5af-4167-9877-bac8afdf4d65",
        cryptoModule: PubNub.CryptoModule.aesCbcCryptoModule({ cipherKey: "secret-123" }),
        userId: user_Id,
    });

    pubnub.addListener({
        status: (statusEvent) => {
            console.log("Status Event:", statusEvent.category);
            if (statusEvent.category === "PNConnectedCategory") {
                console.log("Successfully connected to channel:", appChannel);
            }
        },
        message: (messageEvent) => {
            console.log("Message received:", messageEvent.message);
        },
    });

    pubnub.subscribe({ channels: [appChannel] });
};

setupPubNub();

// Export the PubNub instance for use in other scripts
window.pubnubInstance = pubnub;

function grantAccess(ab)
{
    var userId = ab.id.split("-")[2];
    var readState = document.getElementById("read-user-"+userId).checked;
    var writeState = document.getElementById("write-user-"+userId).checked;
    sendEvent("grant-"+userId+"-"+readState+"-"+writeState);
}

function sendEvent(value)
{
    fetch(value,
        {
            method:"POST",
        })
        .then(response => response.json())
        .then(responseJson =>{
            console.log(responseJson);
            if(responseJson.hasOwnProperty('token'))
            {
                pubnub.setToken(responseJson.token);
                //pubnub.setCipherKey(responseJson.cipher_key);
		        pubnub.setUUID(responseJson.uuid);
                subscribe();
            }
        });
}

function subscribe()
{
    console.log("Trying to subscribe with token");
    const channel = pubnub.channel(appChannel)
    const subscription = channel.subscription();
    subscription.subscribe();
}