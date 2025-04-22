function showAlert(text){
    alert(text);
}

//down here are jokes :)
let counter = 0;
function incrementBClicks(){
    counter++;

    if(counter === 5){
        showAlert("Brute is gae")

        fetch("/set_brute",{method: "POST", headers: { "Content-Type": "application/json"}}).then(res=>res.json()).then(data=>{console.log("session set to wade:", data)}).catch(err=>{console.error("Error setting to wade :(", err);});
    }
}