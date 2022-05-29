function openNav() {
  document.getElementById("menu").style.transform = "translateX(0)";
  console.log("open");
}

function closeNav() {
  document.getElementById("menu").style.transform = "translateX(100%)";
}

function update() {
  document.getElementById('igraph').src += '';
  console.log("updated");
}
