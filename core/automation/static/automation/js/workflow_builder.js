var editor = null;

const WorkflowBuilder = {
    config: {},

    init: function (config) {
        this.config = config;
        // Ensure moduleConfig exists
        this.config.moduleConfig = this.config.moduleConfig || {};
        this.initDrawflow();
        this.attachEvents();
    },

    initDrawflow: function () {
        const id = document.getElementById(this.config.containerId);
        editor = new Drawflow(id);
        editor.reroute = true;
        editor.start();

        if (this.config.initialData) {
            editor.import(this.config.initialData);
            // Re-fill inputs after import because Drawflow doesn't do it automatically
            const nodes = editor.drawflow.drawflow.Home.data;
            Object.keys(nodes).forEach(key => {
                this.updateHTMLFromData(key, nodes[key].data);
                this.attachNodeListeners(key);
            });
        }

        editor.on('nodeCreated', (id) => this.attachNodeListeners(id));
    },

    /**
     * Helper to generate <option> tags from module config
     */
    getTriggerOptions: function () {
        let html = '<option value="">Select an event...</option>';
        const modules = this.config.moduleConfig;

        // Check if modules exist
        if (!modules) {
            console.warn('No module configuration found');
            return html;
        }

        for (const [key, module] of Object.entries(modules)) {
            if (module.triggers && module.triggers.length > 0) {
                html += `<optgroup label="${module.label|| key}">`;
                module.triggers.forEach(trigger => {
                    // Make sure trigger object has required properties
                    if (trigger && trigger.id){
                        // Value is "app.event" e.g. "leads.lead_created"
                        html += `<option value="${key}.${trigger.id}">${trigger.label}</option>`;
                    }
                });
                html += `</optgroup>`;
            }
        }
        return html;
    },

    getActionOptions: function () {
        let html = '<option value="">Select an action...</option>';
        const modules = this.config.moduleConfig;
        // Check if modules exist
        if (!modules) {
            console.warn('No module configuration found');
            return html;
        }

        for (const [key, module] of Object.entries(modules)) {
            if (module.actions && module.actions.length > 0) {
                html += `<optgroup label="${module.label || key}">`;
                module.actions.forEach(action => {
                    // Make sure action object has required properties
                    if (action && action.id) {

                    html += `<option value="${key}.${action.id}">${action.label}</option>`;
                    }
                });
                html += `</optgroup>`;
            }
        }
        return html;
    },

    /**
     * Define Node HTML
     */
    getNodeHTML: function (type) {
        if (type === 'trigger') {
            return `
                <div class="title-box trigger" style="background:#e7f1ff; color:#0d6efd; padding:10px; font-weight:bold; border-bottom:1px solid #ccc;">
                    <i class="fas fa-bolt"></i> When...
                </div>
                <div class="box" style="padding:10px;">
                    <label style="font-size:12px; color:#666;">Application Event</label>
                    <select name="event" class="form-select form-select-sm" df-event style="width:100%;">
                        ${this.getTriggerOptions(data.action)}
                    </select>
                    <!-- Inputs for params can be added here or dynamically -->
                    <label style="font-size:12px; color:#666; margin-top:5px;">Target/Title</label>
                    <input type="text" name="target" class="form-control form-control-sm" df-target placeholder="Task title / Email subject" value="${data.target || ''}">
                </div>
            `;
        }
        else if (type === 'condition') {
            return `
                <div class="title-box condition" style="background:#fff3cd; color:#856404; padding:10px; font-weight:bold; border-bottom:1px solid #ccc;">
                    <i class="fas fa-code-branch"></i> If / Else
                </div>
                <div class="box" style="padding:10px;">
                    <label style="font-size:12px; color:#666;">Field</label>
                    <input type="text" name="field" class="form-control form-control-sm" df-field value="${data.field || ''}">
                    <label style="font-size:12px; color:#666;">Operator</label>
                    <select name="operator" class="form-select form-select-sm" df-operator style="width:100%;">
                        <option value="eq" ${data.operator === 'eq' ? 'selected' : ''}>Equals</option>
                        <option value="gt" ${data.operator === 'gt' ? 'selected' : ''}>Greater Than</option>
                        <option value="lt" ${data.operator === 'lt' ? 'selected' : ''}>Less Than</option>
                        <option value="contains" ${data.operator === 'contains' ? 'selected' : ''}>Contains</option>
                    </select>
                    <label style="font-size:12px; color:#666;">Value</label>
                    <input type="text" name="value" class="form-control form-control-sm" df-value value="${data.value || ''}">
                </div>
            `;
        }
        // Fallback for predefined nodes like send_email, create_task, etc.
        else {
            // Map predefined node types to appropriate labels and icons
            const nodeTypes = {
                'send_email': { 
                    label: 'Send Email', 
                    icon: 'fa-envelope',
                    colorClass: 'action',
                    bgColor: '#d1e7dd',
                    textColor: '#0f5132'
                },
                'create_task': { 
                    label: 'Create Task', 
                    icon: 'fa-tasks',
                    colorClass: 'action',
                    bgColor: '#d1e7dd',
                    textColor: '#0f5132'
                },
                'update_field': { 
                    label: 'Update Field', 
                    icon: 'fa-edit',
                    colorClass: 'action',
                    bgColor: '#d1e7dd',
                    textColor: '#0f5132'
                },
                'webhook': { 
                    label: 'Webhook', 
                    icon: 'fa-link',
                    colorClass: 'action',
                    bgColor: '#d1e7dd',
                    textColor: '#0f5132'
                }
            };
            
            const nodeInfo = nodeTypes[type] || { 
                label: type, 
                icon: 'fa-cog',
                colorClass: 'action',
                bgColor: '#d1e7dd',
                textColor: '#0f5132'
            };
            
            return `
                <div class="title-box ${nodeInfo.colorClass}" style="background:${nodeInfo.bgColor}; color:${nodeInfo.textColor}; padding:10px; font-weight:bold; border-bottom:1px solid #ccc;">
                    <i class="fas ${nodeInfo.icon}"></i> ${nodeInfo.label}
                </div>
                <div class="box" style="padding:10px;">
                    <label style="font-size:12px; color:#666;">Configuration</label>
                    <input type="text" name="config" class="form-control form-control-sm" df-config placeholder="Configuration details" value="${data.config || ''}">
                </div>
            `;
        }
    },


    addNode: function (type, x, y) {
        if (editor.editor_mode === 'fixed') return;
        // Drawflow specific coordinate math
        x = x * (editor.precanvas.clientWidth / (editor.precanvas.clientWidth * editor.zoom)) - (editor.precanvas.getBoundingClientRect().x * (editor.precanvas.clientWidth / (editor.precanvas.clientWidth * editor.zoom)));
        y = y * (editor.precanvas.clientHeight / (editor.precanvas.clientHeight * editor.zoom)) - (editor.precanvas.getBoundingClientRect().y * (editor.precanvas.clientHeight / (editor.precanvas.clientHeight * editor.zoom)));

        let inputs = 1;
        let outputs = 1;
        
        if (type === 'trigger') {
            inputs = 0;
        } else if (type === 'condition') {
            outputs = 2; // True/false branches
        }

        // Create node with empty data initially
        const nodeId = editor.addNode(type, inputs, outputs, x, y, type, {}, this.getNodeHTML(type, {}));
        
        return nodeId;
    },

    attachEvents: function () {
        document.querySelectorAll('.node-template').forEach(el => {
            el.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('node', e.target.dataset.node);
            });
        });

        const container = document.getElementById(this.config.containerId);
        container.addEventListener('dragover', e => e.preventDefault());
        container.addEventListener('drop', e => {
            e.preventDefault();
            const type = e.dataTransfer.getData('node');
            if (type) this.addNode(type, e.clientX, e.clientY);
        });
    },

    attachNodeListeners: function (id) {
         const node = document.getElementById('node-' + id);
        if (!node) return;
        
        node.querySelectorAll('input, select').forEach(input => {
            // Listen for changes and update internal data immediately
            input.addEventListener('change', () => {
                const data = editor.drawflow.drawflow.Home.data[id].data;
                const key = input.getAttribute('df-' + input.name) || input.name;
                data[key] = input.value;
            });
            input.addEventListener('keyup', () => {
                const data = editor.drawflow.drawflow.Home.data[id].data;
                const key = input.getAttribute('df-' + input.name) || input.name;
                data[key] = input.value;
            });
        });
    },

    updateHTMLFromData: function (id, data) {
        const node = document.getElementById('node-' + id);
        if (!node || !data) return;
        Object.keys(data).forEach(key => {
            const input = node.querySelector(`[name="${key}"]`);
            if (input) input.value = data[key];
        });
    },

    saveWorkflow: function () {
        const name = document.getElementById('workflowName').value;
        const data = editor.export();

        fetch(this.config.saveUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.config.csrfToken
            },
            body: JSON.stringify({
                id: this.config.workflowId, // Send ID if editing
                name: name,
                workflow_data: data
            })
        })
            .then(r => r.json())
            .then(res => {
                if (res.success) {
                    alert('Saved!');
                    if (res.redirect_url) window.location.href = res.redirect_url;
                }
                else alert(res.error);
            });
    },
    
    clearCanvas: function() {
        if (confirm('Are you sure you want to clear the canvas?')) {
            editor.clear();
        }
    },
    
    exportJSON: function() {
        const data = editor.export();
        const dataStr = JSON.stringify(data, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = 'workflow.json';
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
    },
    
    importJSON: function(file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            try {
                const data = JSON.parse(event.target.result);
                editor.clear();
                editor.import(data);
            } catch (e) {
                alert('Invalid JSON file');
            }
        };
        reader.readAsText(file);
    }
};