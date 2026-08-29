(function($){
  'use strict';

  /*
   * AI assistance is deliberately limited to content-writing fields.  The
   * button is injected into both normal Django admin fields and TabularInline
   * rows (where there is no <label> inside the cell).
   */
  const FIELD_MAP = {
    resume: {
      short_desc:'Short Description',
      summary:'Summary',
      skills:'Skills',
      experience:'Experience'
    },
    journey: { short_desc:'Short Description' },
    resumejourney: { description:'Description' },
    profession: { short_desc:'Short Description' },
    service: { description:'Description' },
    testimonial: { quote:'Quote' },
    excellence: { description:'Description' }
  };

  // Django inline formset prefixes / IDs -> model names.
  const INLINE_MODEL_MAP = {
    journeys: 'resumejourney',
    resumejourneys: 'resumejourney',
    excellences: 'excellence',
    services: 'service',
    testimonials: 'testimonial'
  };

  function csrf(){
    const m=document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function pageModel(){
    const m=location.pathname.match(/\/admin\/([^/]+)\/([^/]+)\//);
    return m ? m[2].toLowerCase() : '';
  }

  function modelForWrapper(wrapper){
    const page = pageModel();
    const group = wrapper.closest('.inline-group');
    if(group){
      const id=(group.id || '').replace(/-group$/, '').toLowerCase();
      if(INLINE_MODEL_MAP[id]) return INLINE_MODEL_MAP[id];
      const heading=(group.querySelector('h2')?.textContent || '').trim().toLowerCase();
      if(heading.includes('resume journey')) return 'resumejourney';
      if(heading.includes('excellence')) return 'excellence';
      if(heading.includes('service')) return 'service';
      if(heading.includes('testimonial')) return 'testimonial';
    }
    return page;
  }

  function findInput(wrapper){
    return wrapper.querySelector('textarea:not([type=hidden]), input:not([type=hidden])');
  }

  function getValue(wrapper){
    const editable=wrapper.querySelector('.ck-editor__editable');
    if(editable) return editable.innerText || editable.textContent || '';
    const el=findInput(wrapper);
    return el ? el.value : '';
  }

  function htmlForText(text){
    return (text || '').split(/\n+/).map(function(line){
      const escaped=$('<div>').text(line).html();
      return '<p>'+escaped+'</p>';
    }).join('');
  }

  function setValue(wrapper,text){
    const editable=wrapper.querySelector('.ck-editor__editable');
    const input=findInput(wrapper);
    const html=htmlForText(text);

    // django-ckeditor-5 versions expose the editor instance on the editable
    // element or textarea. Use it when available so the editor's internal
    // model is updated, not just its DOM.
    const candidates=[editable,input].filter(Boolean);
    for(const node of candidates){
      const editor=node.ckeditorInstance || node.__ckeditorInstance || node.editor;
      if(editor && typeof editor.setData === 'function'){
        editor.setData(html);
        if(input){ input.value=html; }
        return true;
      }
    }

    if(editable){
      editable.innerHTML=html;
      editable.dispatchEvent(new Event('input',{bubbles:true}));
      editable.dispatchEvent(new Event('change',{bubbles:true}));
      // Keep the form's textarea synchronized for submit/save.
      if(input){
        input.value=html;
        input.dispatchEvent(new Event('input',{bubbles:true}));
        input.dispatchEvent(new Event('change',{bubbles:true}));
      }
      return true;
    }

    if(input){
      input.value=text;
      input.dispatchEvent(new Event('input',{bubbles:true}));
      input.dispatchEvent(new Event('change',{bubbles:true}));
      return true;
    }
    return false;
  }

  function resumeId(){
    const el=document.querySelector('[name="resume"]');
    return (el && el.value) ? el.value : '';
  }

  function parentInfo(wrapper){
    // Standalone nested models can expose their parent FK. For inline rows,
    // the parent is already represented by the current admin object, so the
    // logged-in user's Resume fallback is used server-side.
    const names=['category','section','certificate','journey'];
    for(const name of names){
      const el=wrapper.querySelector('[name$="-'+name+'"], [name="'+name+'"]');
      if(el && el.value) return {model:name,parent_id:el.value};
    }
    return {model:'',parent_id:''};
  }

  function objectIdFor(wrapper){
    const row=wrapper.closest('.inline-related');
    if(row){
      const id=row.querySelector('input[name$="-id"]');
      if(id && id.value) return id.value;
    }
    const id=document.querySelector('input[name="id"]');
    return id ? id.value : (location.pathname.match(/\/([0-9]+)\/change\/$/)||[])[1] || '';
  }

  function findTargetWrapper(field){
    // Normal admin form rows.
    const direct=document.querySelector('.form-row.field-'+field);
    if(direct) return direct;

    // Tabular inline cells use td.field-<field>.
    const cells=document.querySelectorAll('td.field-'+field+', div.field-'+field);
    if(cells.length) return cells[0];
    return null;
  }

  function addButton(wrapper, field, model){
    if(!wrapper || wrapper.dataset.aiReady) return;
    wrapper.dataset.aiReady='1';

    // Avoid adding to read-only/deleted inline rows.
    if(wrapper.closest('.deleted')) return;

    const target=wrapper.querySelector('.ck-editor__editable') || findInput(wrapper);
    if(!target) return;

    const button=document.createElement('button');
    button.type='button';
    button.className='button ai-inline-assist';
    button.style.margin='4px 0 6px 8px';
    button.style.verticalAlign='middle';
    button.textContent='✨ AI Assist';
    button.title='Generate content with AI';

    const label=wrapper.querySelector('label');
    if(label){
      label.appendChild(button);
    }else{
      // TabularInline: put the button directly in the field cell, before the
      // editor/input so it is visible for every inline row.
      target.parentNode.insertBefore(button,target);
    }

    button.addEventListener('click', async function(){
      const friendly=(FIELD_MAP[model] && FIELD_MAP[model][field]) || field;
      const instruction=window.prompt(
        'What should AI write for '+friendly+'?',
        'Write professional, concise, truthful content suitable for this resume.'
      );
      if(!instruction) return;

      button.disabled=true;
      const original=button.textContent;
      button.textContent='Generating...';

      try{
        const parent=parentInfo(wrapper);
        const body=new URLSearchParams({
          model:model,
          field_name:field,
          object_id:objectIdFor(wrapper),
          resume_id:resumeId(),
          parent_model:parent.model,
          parent_id:parent.parent_id,
          current_content:getValue(wrapper),
          instruction:instruction
        });

        const response=await fetch('/ai/generate/component/',{
          method:'POST',
          headers:{
            'X-CSRFToken':csrf(),
            'X-Requested-With':'XMLHttpRequest',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
          },
          body:body.toString()
        });

        let data={};
        try{ data=await response.json(); }catch(e){ data={}; }
        if(!response.ok) throw new Error(data.error || 'AI generation failed.');

        if(!setValue(wrapper,data.content || '')){
          throw new Error('The AI response was generated, but the form field could not be updated.');
        }

        window.alert(
          'AI content generated successfully.\n\n' +
          'Credits used: '+(data.charged_tokens ?? 0)+'\n' +
          'Credits remaining: '+(data.available_tokens ?? 0)+'\n\n' +
          'Review the content and click Save.'
        );
      }catch(error){
        window.alert(error.message || 'AI generation failed.');
      }finally{
        button.disabled=false;
        button.textContent=original;
      }
    });
  }

  function init(){
    // Add assistants to supported standalone pages and all matching inline
    // fields. We inspect every field rather than relying only on a model-level
    // CSS class, which makes this work with Django's TabularInline markup.
    Object.keys(FIELD_MAP).forEach(function(model){
      Object.keys(FIELD_MAP[model]).forEach(function(field){
        document.querySelectorAll('.form-row.field-'+field+', td.field-'+field+', div.field-'+field).forEach(function(wrapper){
          const resolved=modelForWrapper(wrapper);
          if(resolved===model) addButton(wrapper,field,model);
        });
      });
    });
  }

  $(function(){
    init();
    setTimeout(init,300);
    setTimeout(init,800);
    setTimeout(init,1500);

    // Django admin adds inline rows dynamically when the user clicks
    // "Add another". Re-run the lightweight initializer after additions.
    $(document).on('formset:added', function(){
      setTimeout(init,50);
    });
  });
})(django.jQuery);
