/**
 * Animated Loading Indicators for AI Processing Stages
 * Provides visual feedback during transcript analysis with multiple AI providers
 */

class AILoadingIndicator {
  constructor() {
    this.currentStage = null;
    this.stages = [
      { id: 'upload', name: 'Uploading Transcript', icon: 'fas fa-upload' },
      { id: 'extract', name: 'Extracting Content', icon: 'fas fa-file-text' },
      { id: 'openai', name: 'OpenAI Analysis', icon: 'fas fa-brain' },
      { id: 'anthropic', name: 'Anthropic Analysis', icon: 'fas fa-robot' },
      { id: 'gemini', name: 'Gemini Analysis', icon: 'fas fa-gem' },
      { id: 'notion', name: 'Syncing to Notion', icon: 'fas fa-sync' },
      { id: 'complete', name: 'Analysis Complete', icon: 'fas fa-check-circle' }
    ];
    this.initialize();
  }

  initialize() {
    this.createStyles();
    this.createModal();
  }

  createStyles() {
    const styleElement = document.createElement('style');
    styleElement.textContent = `
      .ai-loading-modal {
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(4px);
      }

      .ai-loading-content {
        background: var(--card-background);
        border-radius: 12px;
        padding: 2rem;
        max-width: 500px;
        width: 90%;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        border: 1px solid var(--border-color);
      }

      .ai-loading-header {
        text-align: center;
        margin-bottom: 2rem;
      }

      .ai-loading-title {
        color: var(--text-primary);
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
      }

      .ai-loading-subtitle {
        color: var(--text-secondary);
        font-size: 0.875rem;
      }

      .ai-stages-container {
        margin-bottom: 2rem;
      }

      .ai-stage {
        display: flex;
        align-items: center;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-radius: 8px;
        transition: all 0.3s ease;
        background: var(--background-hover);
        border: 1px solid transparent;
      }

      .ai-stage.active {
        background: var(--primary-color);
        color: white;
        border-color: var(--primary-hover);
        transform: scale(1.02);
      }

      .ai-stage.completed {
        background: var(--success-color);
        color: white;
        border-color: var(--success-color);
      }

      .ai-stage.failed {
        background: var(--danger-color);
        color: white;
        border-color: var(--danger-color);
      }

      .ai-stage-icon {
        width: 24px;
        text-align: center;
        margin-right: 1rem;
      }

      .ai-stage-name {
        flex: 1;
        font-weight: 500;
      }

      .ai-stage-status {
        font-size: 0.75rem;
        opacity: 0.8;
      }

      .ai-spinner {
        width: 16px;
        height: 16px;
        border: 2px solid transparent;
        border-top: 2px solid currentColor;
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }

      .ai-progress-bar {
        width: 100%;
        height: 8px;
        background: var(--background-hover);
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 1rem;
      }

      .ai-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--primary-color), var(--primary-hover));
        border-radius: 4px;
        transition: width 0.5s ease;
        width: 0%;
      }

      .ai-estimated-time {
        text-align: center;
        color: var(--text-secondary);
        font-size: 0.875rem;
        margin-bottom: 1rem;
      }

      .ai-processing-details {
        background: var(--background-color);
        border-radius: 6px;
        padding: 1rem;
        margin-top: 1rem;
        border: 1px solid var(--border-color);
      }

      .ai-processing-detail {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
        font-size: 0.875rem;
      }

      .ai-processing-detail:last-child {
        margin-bottom: 0;
      }

      .ai-cancel-button {
        background: transparent;
        border: 1px solid var(--border-color);
        color: var(--text-secondary);
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.875rem;
      }

      .ai-cancel-button:hover {
        background: var(--background-hover);
        border-color: var(--text-secondary);
      }

      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }

      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
      }

      .ai-stage.active .ai-stage-icon {
        animation: pulse 1.5s ease-in-out infinite;
      }

      /* Dark theme adjustments */
      [data-theme="dark"] .ai-loading-content {
        background: #1e1e1e;
        border-color: #343a40;
      }

      [data-theme="dark"] .ai-processing-details {
        background: #121212;
      }

      /* Responsive design */
      @media (max-width: 576px) {
        .ai-loading-content {
          padding: 1.5rem;
          margin: 1rem;
        }

        .ai-stage {
          padding: 0.75rem;
        }

        .ai-loading-title {
          font-size: 1.25rem;
        }
      }
    `;
    document.head.appendChild(styleElement);
  }

  createModal() {
    const modal = document.createElement('div');
    modal.id = 'aiLoadingModal';
    modal.className = 'modal fade ai-loading-modal';
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-hidden', 'true');
    modal.setAttribute('data-bs-backdrop', 'static');
    modal.setAttribute('data-bs-keyboard', 'false');

    modal.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="ai-loading-content">
          <div class="ai-loading-header">
            <h4 class="ai-loading-title">Processing Transcript</h4>
            <p class="ai-loading-subtitle">AI analysis in progress</p>
          </div>

          <div class="ai-progress-bar">
            <div class="ai-progress-fill" id="aiProgressFill"></div>
          </div>

          <div class="ai-estimated-time" id="aiEstimatedTime">
            Estimated time: 2-3 minutes
          </div>

          <div class="ai-stages-container" id="aiStagesContainer">
            <!-- Stages will be populated dynamically -->
          </div>

          <div class="ai-processing-details" id="aiProcessingDetails" style="display: none;">
            <div class="ai-processing-detail">
              <span>Current Provider:</span>
              <span id="aiCurrentProvider">-</span>
            </div>
            <div class="ai-processing-detail">
              <span>Tokens Processed:</span>
              <span id="aiTokensProcessed">-</span>
            </div>
            <div class="ai-processing-detail">
              <span>Analysis Type:</span>
              <span id="aiAnalysisType">Comprehensive Clinical</span>
            </div>
          </div>

          <div class="text-center mt-3">
            <button class="ai-cancel-button" onclick="aiLoadingIndicator.cancel()" style="display: none;" id="aiCancelButton">
              Cancel Processing
            </button>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    this.modal = new bootstrap.Modal(modal);
  }

  show(filename = 'transcript') {
    this.filename = filename;
    this.startTime = Date.now();
    this.currentStageIndex = 0;
    this.renderStages();
    this.updateProgress(0);
    this.modal.show();
    
    // Start the first stage
    this.nextStage();
  }

  hide() {
    this.modal.hide();
  }

  renderStages() {
    const container = document.getElementById('aiStagesContainer');
    container.innerHTML = this.stages.map((stage, index) => `
      <div class="ai-stage" id="aiStage${stage.id}">
        <div class="ai-stage-icon">
          <i class="${stage.icon}"></i>
        </div>
        <div class="ai-stage-name">${stage.name}</div>
        <div class="ai-stage-status" id="aiStageStatus${stage.id}">Pending</div>
      </div>
    `).join('');
  }

  nextStage() {
    if (this.currentStageIndex > 0) {
      this.completeStage(this.currentStageIndex - 1);
    }

    if (this.currentStageIndex < this.stages.length) {
      this.setActiveStage(this.currentStageIndex);
      this.updateProgress((this.currentStageIndex / this.stages.length) * 100);
      this.updateEstimatedTime();
      this.currentStageIndex++;
    }
  }

  setActiveStage(index) {
    const stage = this.stages[index];
    const element = document.getElementById(`aiStage${stage.id}`);
    const status = document.getElementById(`aiStageStatus${stage.id}`);
    
    element.className = 'ai-stage active';
    status.innerHTML = '<div class="ai-spinner"></div>';
    
    // Update current provider
    if (['openai', 'anthropic', 'gemini'].includes(stage.id)) {
      document.getElementById('aiCurrentProvider').textContent = stage.name;
      document.getElementById('aiProcessingDetails').style.display = 'block';
    }
  }

  completeStage(index) {
    const stage = this.stages[index];
    const element = document.getElementById(`aiStage${stage.id}`);
    const status = document.getElementById(`aiStageStatus${stage.id}`);
    
    element.className = 'ai-stage completed';
    status.innerHTML = '<i class="fas fa-check"></i>';
  }

  failStage(index, error = 'Failed') {
    const stage = this.stages[index];
    const element = document.getElementById(`aiStage${stage.id}`);
    const status = document.getElementById(`aiStageStatus${stage.id}`);
    
    element.className = 'ai-stage failed';
    status.innerHTML = '<i class="fas fa-times"></i>';
    status.title = error;
  }

  updateProgress(percentage) {
    const fill = document.getElementById('aiProgressFill');
    fill.style.width = `${percentage}%`;
  }

  updateEstimatedTime() {
    const elapsed = (Date.now() - this.startTime) / 1000;
    const totalStages = this.stages.length;
    const completedStages = this.currentStageIndex;
    
    if (completedStages > 1) {
      const avgTimePerStage = elapsed / completedStages;
      const remainingStages = totalStages - completedStages;
      const estimatedRemaining = Math.ceil(avgTimePerStage * remainingStages);
      
      document.getElementById('aiEstimatedTime').textContent = 
        `Estimated time remaining: ${estimatedRemaining}s`;
    }
  }

  updateTokenCount(tokens) {
    document.getElementById('aiTokensProcessed').textContent = tokens.toLocaleString();
  }

  complete() {
    this.updateProgress(100);
    this.completeStage(this.stages.length - 1);
    
    setTimeout(() => {
      this.hide();
    }, 2000);
  }

  error(stageId, message) {
    const stageIndex = this.stages.findIndex(s => s.id === stageId);
    if (stageIndex !== -1) {
      this.failStage(stageIndex, message);
    }
    
    document.getElementById('aiCancelButton').style.display = 'block';
  }

  cancel() {
    if (confirm('Are you sure you want to cancel the AI processing?')) {
      this.hide();
      // Emit cancel event
      document.dispatchEvent(new CustomEvent('aiProcessingCancelled'));
    }
  }
}

// Initialize the loading indicator
let aiLoadingIndicator;
document.addEventListener('DOMContentLoaded', () => {
  aiLoadingIndicator = new AILoadingIndicator();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AILoadingIndicator;
}