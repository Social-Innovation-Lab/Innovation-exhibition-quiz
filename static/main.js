(function(){
  const form = document.getElementById('quizForm');
  if(!form) return;
  const qids = [...new Set([...form.querySelectorAll('input[type=radio]')].map(i => i.name))];
  const answered = new Set();
  const ansCount = document.getElementById('ansCount');
  const barFill = document.getElementById('barFill');
  const submitBtn = document.getElementById('submitBtn');

  form.addEventListener('change', (e)=>{
    if(e.target.type === 'radio'){
      answered.add(e.target.name);
      const count = answered.size;
      ansCount.textContent = count;
      barFill.style.width = ((count/qids.length)*100).toFixed(1)+'%';
      submitBtn.disabled = count < qids.length;
    }
  });

  // Prevent accidental back/refresh
  let submitted = false;
  form.addEventListener('submit', ()=>{ submitted = true; submitBtn.disabled = true; submitBtn.textContent='Submitting…'; });
  window.addEventListener('beforeunload', (e)=>{ if(!submitted){ e.preventDefault(); e.returnValue=''; } });

  // Prevent pinch zoom double-tap shenanigans
  document.addEventListener('gesturestart', e => e.preventDefault());
})();
