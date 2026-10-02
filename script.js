function openModal(){
  const modal=document.getElementById("taskModal");
  if(modal) modal.classList.add("open");
}
function closeModal(){
  const modal=document.getElementById("taskModal");
  if(modal) modal.classList.remove("open");
}
document.addEventListener("click",function(e){
  const modal=document.getElementById("taskModal");
  if(modal && e.target===modal) closeModal();
});
document.addEventListener("keydown",function(e){
  if(e.key==="Escape") closeModal();
});
function filterTasks(){
  const search=(document.getElementById("searchInput")?.value || "").toLowerCase();
  const status=document.getElementById("statusFilter")?.value || "All";
  const priority=document.getElementById("priorityFilter")?.value || "All";
  document.querySelectorAll(".task-card").forEach(card=>{
    const matchSearch=card.dataset.title.includes(search);
    const matchStatus=status==="All" || card.dataset.status===status;
    const matchPriority=priority==="All" || card.dataset.priority===priority;
    card.style.display=(matchSearch && matchStatus && matchPriority) ? "" : "none";
  });
}
["searchInput","statusFilter","priorityFilter"].forEach(id=>{
  document.getElementById(id)?.addEventListener("input",filterTasks);
  document.getElementById(id)?.addEventListener("change",filterTasks);
});
setTimeout(()=>document.querySelectorAll(".toast").forEach(t=>t.remove()),3500);
