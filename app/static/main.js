window.addEventListener("load",()=>{
    element = document.getElementById("origin");
    element.addEventListener("change",()=>{

        console.log(event.target.value);
    })
})
