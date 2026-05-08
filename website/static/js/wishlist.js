function allowDrop(ev) {
  ev.preventDefault();
}

function drag(ev) {
  ev.dataTransfer.setData("text", ev.currentTarget.id);
}

function drop(ev) {
  ev.preventDefault();

  const data = ev.dataTransfer.getData("text");
  const draggedElement = document.getElementById(data);
  const column = ev.target.closest(".rm-priority-col");

  if (!draggedElement || !column) return;

  const targetList = column.querySelector("ul");
  const itemId = draggedElement.getAttribute("data-item-id");
  const priority = column.getAttribute("data-priority");

  if (!targetList || !itemId || !priority) return;

  targetList.appendChild(draggedElement);

  fetch("/wishlist/items/" + itemId + "/priority", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ priority: priority }),
  }).catch(function () {});
}
