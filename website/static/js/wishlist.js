function allowDrop(ev) {
    ev.preventDefault();
}

function drag(ev) {
    ev.dataTransfer.setData("text", ev.target.id);
}

function drop(ev) {
    ev.preventDefault();
    const data = ev.dataTransfer.getData("text");
    const draggedElement = document.getElementById(data);
    

    const column = ev.target.closest(".rm-priority-col");
    
    if (column) {
        const targetList = column.querySelector("ul");
        targetList.appendChild(draggedElement);
    }
}