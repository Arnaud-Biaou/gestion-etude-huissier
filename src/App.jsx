import React, { useState, useEffect, useRef } from 'react';
import { Search, Bell, User, Menu, X, Home, FolderOpen, FileText, DollarSign, PiggyBank, Calculator, Users, HardDrive, Building2, Calendar, ChevronRight, ChevronLeft, Plus, Filter, Download, Upload, Edit, Trash2, Eye, EyeOff, Clock, CheckCircle, AlertCircle, Archive, MoreVertical, TrendingUp, TrendingDown, Briefcase, Scale, Gavel, Phone, Mail, MapPin, Check, ArrowRight, ArrowLeft, Save, Printer, Settings, Shield, QrCode, MessageSquare, Send, Bot, Folder, File, ChevronDown, ChevronUp, UserPlus, Building, Globe, CreditCard, Hash, Lock, Unlock, Key, Copy, RefreshCw, Percent, Receipt, FileSignature, Zap, Target, BarChart3, PieChart, Activity, Layers, GitBranch, AlertTriangle, Info, HelpCircle, Mic, Paperclip, Image, Video, Camera, MapPinned, Navigation, History } from 'lucide-react';

// ============================================
// STYLES CSS COMPLETS
// ============================================
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Source+Sans+3:wght@300;400;500;600;700&display=swap');
  :root {
    --primary: #1a365d;
    --primary-light: #2c5282;
    --primary-dark: #0f2744;
    --accent: #c6a962;
    --accent-light: #d4bc7c;
    --accent-dark: #a68b3d;
    --success: #2f855a;
    --success-light: #48bb78;
    --warning: #c05621;
    --warning-light: #ed8936;
    --danger: #c53030;
    --danger-light: #fc8181;
    --info: #2b6cb0;
    --info-light: #4299e1;
    --neutral-50: #f8fafc;
    --neutral-100: #f1f5f9;
    --neutral-200: #e2e8f0;
    --neutral-300: #cbd5e1;
    --neutral-400: #94a3b8;
    --neutral-500: #64748b;
    --neutral-600: #475569;
    --neutral-700: #334155;
    --neutral-800: #1e293b;
    --neutral-900: #0f172a;
    --font-display: 'Cormorant Garamond', serif;
    --font-body: 'Source Sans 3', sans-serif;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
    --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: var(--font-body); background: var(--neutral-100); color: var(--neutral-800); line-height: 1.6; }
  .app-container { display: flex; min-height: 100vh; }
  
  /* Sidebar & Layout */
  .sidebar { width: 280px; background: linear-gradient(180deg, var(--primary-dark) 0%, var(--primary) 100%); color: white; display: flex; flex-direction: column; position: fixed; height: 100vh; z-index: 100; transition: transform 0.3s ease; }
  .sidebar.collapsed { transform: translateX(-280px); }
  .sidebar-header { padding: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
  .logo { display: flex; align-items: center; gap: 12px; }
  .logo-icon { width: 48px; height: 48px; background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%); border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; font-family: var(--font-display); font-weight: 700; font-size: 18px; color: var(--primary-dark); }
  .logo-text { font-family: var(--font-display); font-size: 18px; font-weight: 600; letter-spacing: 0.5px; }
  .logo-subtitle { font-size: 10px; opacity: 0.7; text-transform: uppercase; letter-spacing: 1px; margin-top: 2px; }
  .sidebar-nav { flex: 1; padding: 12px 8px; overflow-y: auto; }
  .nav-section { margin-bottom: 16px; }
  .nav-section-title { font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.5; padding: 8px 12px; font-weight: 600; }
  .nav-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: var(--radius-md); cursor: pointer; transition: all 0.2s ease; font-size: 13px; font-weight: 500; color: rgba(255,255,255,0.7); }
  .nav-item:hover { background: rgba(255,255,255,0.1); color: white; }
  .nav-item.active { background: rgba(198, 169, 98, 0.2); color: var(--accent-light); border-left: 3px solid var(--accent); margin-left: -3px; }
  .nav-badge { margin-left: auto; background: var(--accent); color: var(--primary-dark); font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 10px; }
  .sidebar-footer { padding: 12px; border-top: 1px solid rgba(255,255,255,0.1); }
  .user-card { display: flex; align-items: center; gap: 10px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: var(--radius-md); }
  .user-avatar { width: 36px; height: 36px; background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 13px; color: var(--primary-dark); }
  .user-info { flex: 1; }
  
  /* MAIN CONTENT */
  .main-content { flex: 1; margin-left: 280px; display: flex; flex-direction: column; }
  .topbar { height: 64px; background: white; border-bottom: 1px solid var(--neutral-200); display: flex; align-items: center; padding: 0 24px; gap: 20px; position: sticky; top: 0; z-index: 50; }
  .menu-toggle { display: none; background: none; border: none; cursor: pointer; padding: 8px; color: var(--neutral-600); }
  @media (max-width: 1024px) {
    .menu-toggle { display: flex; }
    .sidebar { transform: translateX(-280px); }
    .sidebar.open { transform: translateX(0); }
    .main-content { margin-left: 0; }
  }
  .page-title { font-family: var(--font-display); font-size: 22px; font-weight: 600; color: var(--primary); }
  .page-content { flex: 1; padding: 24px; overflow-y: auto; }
  .search-bar { flex: 1; max-width: 400px; position: relative; }
  .search-bar input { width: 100%; padding: 10px 16px 10px 40px; border: 1px solid var(--neutral-200); border-radius: var(--radius-lg); font-size: 13px; background: var(--neutral-50); }
  .search-bar svg { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--neutral-400); width: 18px; height: 18px; }
  .topbar-actions { display: flex; align-items: center; gap: 8px; }
  .icon-btn { width: 38px; height: 38px; border: none; background: var(--neutral-100); border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--neutral-600); position: relative; }

  /* COMMON UI */
  .card { background: white; border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); border: 1px solid var(--neutral-200); margin-bottom: 20px; }
  .card-header { padding: 16px 20px; border-bottom: 1px solid var(--neutral-100); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
  .card-title { font-family: var(--font-display); font-size: 16px; font-weight: 600; color: var(--primary); }
  .card-body { padding: 20px; }
  .btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: var(--radius-md); font-size: 13px; font-weight: 600; cursor: pointer; border: none; font-family: var(--font-body); white-space: nowrap; transition: all 0.2s; }
  .btn-primary { background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%); color: white; }
  .btn-secondary { background: var(--neutral-100); color: var(--neutral-700); border: 1px solid var(--neutral-200); }
  .btn-accent { background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%); color: var(--primary-dark); }
  .btn-danger { background: var(--danger); color: white; }
  .btn-success { background: var(--success); color: white; }
  .btn-sm { padding: 6px 10px; font-size: 12px; }
  .btn-icon { width: 32px; height: 32px; padding: 0; justify-content: center; }

  /* FORMS & TABLES */
  .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
  .form-group { display: flex; flex-direction: column; gap: 6px; }
  .form-group.full-width { grid-column: 1 / -1; }
  .form-label { font-size: 12px; font-weight: 600; color: var(--neutral-700); }
  .form-input, .form-select, .form-textarea { padding: 10px 14px; border: 1px solid var(--neutral-300); border-radius: var(--radius-md); font-size: 13px; background: white; width: 100%; }
  .form-section-title { font-family: var(--font-display); font-size: 15px; font-weight: 600; color: var(--primary); margin: 20px 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--neutral-200); grid-column: 1 / -1; }
  .toggle-group { display: flex; gap: 8px; flex-wrap: wrap; }
  .toggle-option { padding: 8px 16px; border: 2px solid var(--neutral-200); border-radius: var(--radius-md); font-size: 13px; font-weight: 500; cursor: pointer; background: white; }
  .toggle-option.active { border-color: var(--primary); background: rgba(26, 54, 93, 0.05); color: var(--primary); }
  .table-container { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; padding: 12px 14px; font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--neutral-500); background: var(--neutral-50); border-bottom: 1px solid var(--neutral-200); }
  td { padding: 14px; border-bottom: 1px solid var(--neutral-100); font-size: 13px; }

  /* INVOICE */
  .invoice-paper { background: white; width: 100%; min-height: 800px; padding: 40px; box-shadow: var(--shadow-md); font-size: 12px; position: relative; }
  .invoice-header { display: flex; justify-content: space-between; margin-bottom: 40px; border-bottom: 2px solid var(--primary); padding-bottom: 20px; }
  .invoice-logo { width: 80px; height: 80px; background: var(--neutral-100); display: flex; align-items: center; justify-content: center; font-weight: bold; color: var(--primary); }
  .invoice-title { font-size: 24px; font-family: var(--font-display); color: var(--primary); text-transform: uppercase; font-weight: 700; text-align: right; }
  .invoice-status { font-size: 14px; color: var(--danger); font-weight: bold; text-align: right; margin-top: 5px; text-transform: uppercase; border: 2px dashed var(--danger); display: inline-block; padding: 4px 8px; transform: rotate(-5deg); }
  .invoice-status.normalisee { color: var(--success); border-color: var(--success); }
  .invoice-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
  .invoice-table th { background: var(--primary); color: white; padding: 8px; text-align: left; font-size: 11px; }
  .invoice-table td { border-bottom: 1px solid var(--neutral-200); padding: 8px; vertical-align: top; }
  .invoice-total-row { display: flex; justify-content: space-between; padding: 8px 0; font-weight: 500; }
  .invoice-final-total { font-size: 16px; font-weight: 700; color: var(--primary); border-top: 2px solid var(--primary); padding-top: 10px; margin-top: 10px; }

  /* DOSSIER CARD (PHYSICAL) */
  .dossier-card-paper { width: 100%; max-width: 600px; margin: 0 auto; background: white; border: 4px double var(--primary); padding: 30px; position: relative; font-family: var(--font-body); }
  .dossier-card-header { text-align: center; border-bottom: 2px solid var(--accent); padding-bottom: 15px; margin-bottom: 20px; }
  .dossier-ref { font-family: var(--font-display); font-size: 32px; font-weight: 800; color: var(--primary); text-align: center; margin: 10px 0; background: var(--neutral-50); padding: 10px; border-radius: 8px; letter-spacing: 1px; }
  .dossier-parties-box { display: flex; gap: 20px; margin-bottom: 20px; }
  .dossier-party-col { flex: 1; border: 1px solid var(--neutral-300); padding: 15px; border-radius: 8px; }
  .dossier-party-title { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; color: var(--neutral-500); margin-bottom: 5px; }
  .dossier-party-name { font-size: 16px; font-weight: 700; color: var(--neutral-800); margin-bottom: 5px; }
  .dossier-details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; font-size: 13px; }
  .dossier-detail-item { display: flex; flex-direction: column; }
  .dossier-label { font-weight: 600; color: var(--neutral-500); font-size: 11px; }
  .dossier-value { font-weight: 600; color: var(--primary); font-size: 14px; }
  .dossier-footer { display: flex; justify-content: space-between; align-items: center; border-top: 2px solid var(--neutral-200); padding-top: 15px; }

  /* UTILS */
  .alert { padding: 12px 16px; border-radius: var(--radius-md); display: flex; align-items: flex-start; gap: 12px; font-size: 13px; margin-bottom: 16px; }
  .alert-info { background: rgba(43, 108, 176, 0.1); border: 1px solid rgba(43, 108, 176, 0.2); color: var(--info); }
  .alert-warning { background: rgba(192, 86, 33, 0.1); border: 1px solid rgba(192, 86, 33, 0.2); color: var(--warning); }
  .alert-success { background: rgba(47, 133, 90, 0.1); border: 1px solid rgba(47, 133, 90, 0.2); color: var(--success); }
  .status-badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
  .status-badge.active { background: rgba(47, 133, 90, 0.1); color: var(--success); }
  .status-badge.contentieux { background: rgba(43, 108, 176, 0.1); color: var(--info); }
  .status-badge.urgent { background: rgba(197, 48, 48, 0.1); color: var(--danger); }
  
  /* PROGRESS */
  .stepper { display: flex; align-items: center; justify-content: center; margin-bottom: 32px; padding: 0 16px; }
  .step { display: flex; flex-direction: column; align-items: center; position: relative; flex: 1; max-width: 160px; }
  .step-circle { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; transition: all 0.3s ease; position: relative; z-index: 2; }
  .step.completed .step-circle { background: var(--success); color: white; }
  .step.active .step-circle { background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%); color: white; box-shadow: 0 4px 15px rgba(26, 54, 93, 0.3); }
  .step.pending .step-circle { background: var(--neutral-200); color: var(--neutral-500); }
  .step-label { margin-top: 8px; font-size: 11px; font-weight: 500; color: var(--neutral-500); text-align: center; }
  .step-line { position: absolute; top: 20px; left: calc(50% + 24px); width: calc(100% - 48px); height: 3px; background: var(--neutral-200); z-index: 1; }
  .step.completed .step-line { background: var(--success); }
  .progress-bar-container { margin-bottom: 24px; }
  .progress-bar { height: 6px; background: var(--neutral-200); border-radius: 3px; overflow: hidden; }
  .progress-bar-fill { height: 100%; background: linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%); border-radius: 3px; transition: width 0.5s ease; }

  /* CHATBOT */
  .chatbot-container { position: fixed; bottom: 24px; right: 24px; z-index: 150; }
  .chatbot-window { position: absolute; bottom: 70px; right: 0; width: 380px; height: 520px; background: white; border-radius: var(--radius-xl); box-shadow: var(--shadow-lg); display: flex; flex-direction: column; overflow: hidden; animation: slideUp 0.3s ease; }
  @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
  .chatbot-header { padding: 16px 20px; background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%); color: white; display: flex; align-items: center; gap: 12px; }
  .chatbot-messages { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
  .chat-message { max-width: 85%; padding: 10px 14px; border-radius: var(--radius-lg); font-size: 13px; }
  .chat-message.bot { background: var(--neutral-100); align-self: flex-start; }
  .chat-message.user { background: var(--primary); color: white; align-self: flex-end; }
  .chatbot-input-area { padding: 12px 16px; border-top: 1px solid var(--neutral-200); display: flex; gap: 8px; }

  /* MODAL & TABS */
  .modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 200; }
  .modal { background: white; border-radius: var(--radius-xl); width: 100%; max-width: 900px; max-height: 90vh; overflow: hidden; display: flex; flex-direction: column; }
  .modal.large { max-width: 1100px; }
  .modal-header { padding: 20px 24px; border-bottom: 1px solid var(--neutral-200); display: flex; justify-content: space-between; align-items: center; }
  .modal-title { font-family: var(--font-display); font-size: 18px; font-weight: 600; color: var(--primary); }
  .modal-close { background: none; border: none; cursor: pointer; color: var(--neutral-500); }
  .modal-body { padding: 24px; overflow-y: auto; flex: 1; }
  .modal-footer { padding: 16px 24px; border-top: 1px solid var(--neutral-200); display: flex; justify-content: space-between; }
  .tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--neutral-200); margin-bottom: 20px; overflow-x: auto; }
  .tab { padding: 10px 16px; font-size: 13px; font-weight: 500; color: var(--neutral-500); cursor: pointer; border-bottom: 2px solid transparent; background: none; border-top: none; border-left: none; border-right: none; white-space: nowrap; }
  .tab.active { color: var(--primary); border-bottom-color: var(--primary); }

  /* SPACE UTILITIES */
  .space-y-4 > * + * { margin-top: 16px; }
  .space-y-6 > * + * { margin-top: 24px; }
  .flex { display: flex; }
  .gap-2 { gap: 8px; }
  .gap-4 { gap: 16px; }
  .gap-6 { gap: 24px; }
  .justify-between { justify-content: space-between; }
  .items-center { align-items: center; }
  .grid { display: grid; }
  .grid-cols-1 { grid-template-columns: repeat(1, 1fr); }
  @media (min-width: 1024px) { .lg\\:col-span-1 { grid-column: span 1; } .lg\\:col-span-2 { grid-column: span 2; } }
  .w-full { width: 100%; }
  .text-center { text-align: center; }
  .font-bold { font-weight: 700; }
  .font-medium { font-weight: 500; }
  .text-xs { font-size: 12px; }
  .text-sm { font-size: 14px; }
  .text-lg { font-size: 18px; }
  .p-3 { padding: 12px; }
  .p-4 { padding: 16px; }
  .mt-2 { margin-top: 8px; }
  .mt-4 { margin-top: 16px; }
  .mt-6 { margin-top: 24px; }
  .mb-2 { margin-bottom: 8px; }
  .mb-3 { margin-bottom: 12px; }
  .rounded-lg { border-radius: 8px; }
  .border { border: 1px solid var(--neutral-200); }
  .bg-white { background: white; }
  .bg-gray-50 { background: var(--neutral-50); }
  .overflow-y-auto { overflow-y: auto; }
  .h-96 { height: 384px; }
  .whitespace-pre-wrap { white-space: pre-wrap; }

  /* PRINT */
  @media print {
    .sidebar, .topbar, .chatbot-container, .no-print { display: none !important; }
    .main-content { margin: 0; }
    .page-content { padding: 0; }
    .invoice-paper, .dossier-card-paper { box-shadow: none; border: 2px solid black; }
    .dossier-card-paper { border: 4px double black; }
    body { background: white; }
  }

  /* ADVANCED DASHBOARD STYLES */
  .dashboard-header {
    background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
    border-radius: var(--radius-xl);
    padding: 24px 32px;
    color: white;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
  }
  .dashboard-header h1 {
    font-family: var(--font-display);
    font-size: 28px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  .dashboard-header .datetime {
    display: flex;
    align-items: center;
    gap: 24px;
    font-size: 14px;
    opacity: 0.9;
  }
  .dashboard-header .clock {
    font-size: 32px;
    font-weight: 700;
    font-family: var(--font-display);
  }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 24px;
  }
  @media (max-width: 1200px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 768px) { .kpi-grid { grid-template-columns: 1fr; } }

  .kpi-card {
    background: white;
    border-radius: var(--radius-lg);
    padding: 20px;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--neutral-200);
    display: flex;
    align-items: center;
    gap: 16px;
    transition: all 0.2s ease;
    cursor: pointer;
  }
  .kpi-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
  }
  .kpi-icon {
    width: 56px;
    height: 56px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .kpi-icon.blue { background: rgba(43, 108, 176, 0.1); color: var(--info); }
  .kpi-icon.gold { background: rgba(198, 169, 98, 0.15); color: var(--accent-dark); }
  .kpi-icon.green { background: rgba(47, 133, 90, 0.1); color: var(--success); }
  .kpi-icon.red { background: rgba(197, 48, 48, 0.1); color: var(--danger); }
  .kpi-icon.purple { background: rgba(128, 90, 213, 0.1); color: #805ad5; }
  .kpi-icon.orange { background: rgba(237, 137, 54, 0.1); color: var(--warning); }

  .kpi-content { flex: 1; }
  .kpi-label { font-size: 12px; color: var(--neutral-500); text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
  .kpi-value { font-size: 28px; font-weight: 700; color: var(--primary); line-height: 1.2; }
  .kpi-subtext { font-size: 12px; color: var(--neutral-500); margin-top: 2px; }
  .kpi-subtext.positive { color: var(--success); }
  .kpi-subtext.negative { color: var(--danger); }

  .dashboard-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }
  @media (max-width: 1200px) { .dashboard-grid { grid-template-columns: 1fr; } }

  .widget {
    background: white;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--neutral-200);
    overflow: hidden;
  }
  .widget.full-width { grid-column: 1 / -1; }

  .widget-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--neutral-100);
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--neutral-50);
  }
  .widget-title {
    font-family: var(--font-display);
    font-size: 16px;
    font-weight: 600;
    color: var(--primary);
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .widget-title-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
  }
  .widget-link {
    font-size: 12px;
    color: var(--primary);
    text-decoration: none;
    font-weight: 500;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;
  }
  .widget-link:hover { text-decoration: underline; }

  .widget-body { padding: 20px; }

  .data-table {
    width: 100%;
    font-size: 13px;
  }
  .data-table td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--neutral-100);
  }
  .data-table tr:last-child td { border-bottom: none; }
  .data-table .label { color: var(--neutral-600); }
  .data-table .value { font-weight: 600; text-align: right; color: var(--primary); }
  .data-table .total { font-weight: 700; border-top: 2px solid var(--neutral-200); }

  .progress-mini {
    height: 8px;
    background: var(--neutral-200);
    border-radius: 4px;
    overflow: hidden;
    margin-top: 8px;
  }
  .progress-mini-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
  }
  .progress-mini-fill.blue { background: var(--info); }
  .progress-mini-fill.green { background: var(--success); }
  .progress-mini-fill.gold { background: var(--accent); }
  .progress-mini-fill.red { background: var(--danger); }

  .rdv-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .rdv-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    background: var(--neutral-50);
    border-radius: 8px;
    border-left: 3px solid var(--info);
  }
  .rdv-item.audience { border-left-color: var(--danger); }
  .rdv-item.client { border-left-color: var(--success); }
  .rdv-item.constat { border-left-color: var(--warning); }
  .rdv-time { font-weight: 700; color: var(--primary); min-width: 50px; }
  .rdv-details { flex: 1; }
  .rdv-title { font-weight: 500; font-size: 13px; }
  .rdv-dossier { font-size: 11px; color: var(--neutral-500); }

  .task-list { display: flex; flex-direction: column; gap: 6px; }
  .task-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid var(--neutral-100);
    font-size: 13px;
  }
  .task-item:last-child { border-bottom: none; }
  .task-checkbox {
    width: 18px;
    height: 18px;
    border: 2px solid var(--neutral-300);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
  }
  .task-checkbox.done {
    background: var(--success);
    border-color: var(--success);
    color: white;
  }
  .task-title { flex: 1; }
  .task-title.done { text-decoration: line-through; color: var(--neutral-400); }
  .task-urgent { color: var(--danger); font-size: 10px; font-weight: 600; text-transform: uppercase; }

  .alerts-panel { display: flex; flex-direction: column; gap: 12px; }
  .alert-section { margin-bottom: 8px; }
  .alert-section-title {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .alert-section-title.urgent { color: var(--danger); }
  .alert-section-title.important { color: var(--warning); }
  .alert-section-title.info { color: var(--info); }

  .alert-item {
    font-size: 13px;
    padding: 8px 12px;
    border-radius: 6px;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .alert-item.urgent { background: rgba(197, 48, 48, 0.08); color: var(--danger); }
  .alert-item.important { background: rgba(237, 137, 54, 0.08); color: var(--warning); }
  .alert-item.info { background: rgba(43, 108, 176, 0.08); color: var(--info); }

  .quick-actions {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    background: white;
    border-radius: var(--radius-xl);
    box-shadow: 0 8px 30px rgba(0,0,0,0.15);
    padding: 12px 24px;
    display: flex;
    gap: 12px;
    z-index: 50;
    border: 1px solid var(--neutral-200);
  }
  .quick-action-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 16px;
    border-radius: var(--radius-md);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    border: 1px solid var(--neutral-200);
    background: white;
    color: var(--neutral-700);
    transition: all 0.2s;
  }
  .quick-action-btn:hover {
    background: var(--neutral-100);
    border-color: var(--primary);
    color: var(--primary);
  }
  .quick-action-btn.primary {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
    color: white;
    border: none;
  }
  .quick-action-btn.primary:hover {
    box-shadow: 0 4px 12px rgba(26, 54, 93, 0.3);
  }

  .mini-chart {
    display: flex;
    align-items: flex-end;
    gap: 4px;
    height: 40px;
    padding-top: 8px;
  }
  .mini-chart-bar {
    flex: 1;
    background: linear-gradient(180deg, var(--primary) 0%, var(--primary-light) 100%);
    border-radius: 2px;
    min-height: 4px;
    transition: height 0.3s ease;
  }

  .donut-chart {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    position: relative;
  }
  .donut-center {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
  }
  .donut-value { font-size: 18px; font-weight: 700; color: var(--primary); }
  .donut-label { font-size: 9px; color: var(--neutral-500); }

  .stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--neutral-100);
  }
  .stat-row:last-child { border-bottom: none; }
  .stat-label { color: var(--neutral-600); font-size: 13px; }
  .stat-value { font-weight: 600; color: var(--primary); }
  .stat-value.positive { color: var(--success); }
  .stat-value.negative { color: var(--danger); }

  .trend-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
  }
  .trend-badge.up { background: rgba(47, 133, 90, 0.1); color: var(--success); }
  .trend-badge.down { background: rgba(197, 48, 48, 0.1); color: var(--danger); }

  .refresh-indicator {
    font-size: 11px;
    color: var(--neutral-400);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .refresh-indicator.loading svg { animation: spin 1s linear infinite; }

  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
  .pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--success);
    animation: pulse 2s infinite;
  }
`;

// ============================================
// DONNÉES ET CONSTANTES
// ============================================
const CURRENT_USER = {
  id: 1,
  nom: 'BIAOU Martial Arnaud',
  role: 'admin',
  email: 'mab@etude-biaou.bj'
};

const COLLABORATEURS = [
  { id: 1, nom: 'Me BIAOU Martial', role: 'Huissier' },
  { id: 2, nom: 'ADJOVI Carine', role: 'Clerc Principal' },
  { id: 3, nom: 'HOUNKPATIN Paul', role: 'Clerc' },
  { id: 4, nom: 'DOSSOU Marie', role: 'Secrétaire' },
];

const CATALOGUE_ACTES = [
  { id: 'cmd', label: 'Commandement de payer', tarif: 15000 },
  { id: 'sign_titre', label: 'Signification de titre exécutoire', tarif: 10000 },
  { id: 'pv_saisie', label: 'PV de Saisie-Vente', tarif: 25000 },
  { id: 'pv_carence', label: 'PV de Carence', tarif: 15000 },
  { id: 'denonc', label: 'Dénonciation de saisie', tarif: 12000 },
  { id: 'assign', label: 'Assignation', tarif: 20000 },
  { id: 'sign_ord', label: 'Signification Ordonnance', tarif: 10000 },
  { id: 'certif', label: 'Certificat de non recours', tarif: 5000 },
  { id: 'mainlevee', label: 'Mainlevée', tarif: 15000 },
  { id: 'sommation', label: 'Sommation interpellative', tarif: 12000 },
  { id: 'constat', label: 'Procès-verbal de constat', tarif: 30000 },
];

const TAUX_LEGAL_OHADA = 6;
const TVA_RATE = 18;
const AIB_RATE = 3;

const MODULES_LIST = [
  { id: 'dashboard', label: 'Tableau de bord', icon: Home, category: 'main' },
  { id: 'dossiers', label: 'Dossiers', icon: FolderOpen, badge: 14, category: 'main' },
  { id: 'facturation', label: 'Facturation & MECeF', icon: FileText, category: 'main' },
  { id: 'calcul', label: 'Calcul Recouvrement', icon: Calculator, category: 'main' },
  { id: 'tresorerie', label: 'Trésorerie', icon: PiggyBank, category: 'finance' },
  { id: 'comptabilite', label: 'Comptabilité', icon: BarChart3, category: 'finance' },
  { id: 'rh', label: 'Ressources Humaines', icon: Users, category: 'gestion' },
  { id: 'drive', label: 'Drive', icon: HardDrive, category: 'gestion' },
  { id: 'gerance', label: 'Gérance Immobilière', icon: Building2, category: 'gestion' },
  { id: 'agenda', label: 'Agenda', icon: Calendar, category: 'gestion' },
  { id: 'parametres', label: 'Paramètres', icon: Settings, category: 'admin' },
  { id: 'securite', label: 'Sécurité & Accès', icon: Shield, category: 'admin' },
];

const SOUS_DOSSIERS_TEMPLATE = [
  { nom: 'Projets', icon: FileText },
  { nom: 'Pièces', icon: File },
  { nom: 'Correspondances envoyées', icon: Send },
  { nom: 'Correspondances reçues', icon: Mail },
  { nom: 'Actes finalisés', icon: FileSignature },
  { nom: 'Factures', icon: Receipt },
  { nom: 'Actes externes', icon: Folder },
  { nom: 'Autres', icon: Layers },
];

// ============================================
// COMPOSANTS UTILITAIRES
// ============================================
const Alert = ({ type = 'info', children }) => (
  <div className={`alert alert-${type}`}>
    {type === 'info' && <Info size={18} />}
    {type === 'warning' && <AlertTriangle size={18} />}
    {type === 'success' && <CheckCircle size={18} />}
    <div>{children}</div>
  </div>
);

const ProgressBar = ({ label, percent }) => (
  <div className="progress-bar-container">
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
      <span style={{ fontSize: '12px', fontWeight: '500' }}>{label}</span>
      <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--primary)' }}>{percent}%</span>
    </div>
    <div className="progress-bar">
      <div className="progress-bar-fill" style={{ width: `${percent}%` }} />
    </div>
  </div>
);

const Stepper = ({ steps, currentStep }) => (
  <div className="stepper">
    {steps.map((step, index) => (
      <div key={index} className={`step ${index < currentStep ? 'completed' : index === currentStep ? 'active' : 'pending'}`}>
        <div className="step-circle">{index < currentStep ? <Check size={18} /> : index + 1}</div>
        <div className="step-label">{step}</div>
        {index < steps.length - 1 && <div className="step-line" />}
      </div>
    ))}
  </div>
);

const QRCodeGenerator = ({ data }) => (
  <div style={{ width:'100px', height:'100px', background:'var(--neutral-100)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:'10px', textAlign:'center', border:'1px solid var(--neutral-300)', borderRadius: '8px'}}>
    QR MECeF<br/>{data.id ? data.id.substring(0,8)+'...' : '...'}
  </div>
);

// ============================================
// COMPOSANT: CARTE DOSSIER PHYSIQUE
// ============================================
const DossierPhysicalCard = ({ dossier, collaborateur }) => {
  return (
    <div className="dossier-card-paper">
      <div className="dossier-card-header">
        <div style={{fontSize:'14px', fontWeight:'bold', color:'var(--primary)', textTransform:'uppercase'}}>Étude de Maître BIAOU</div>
        <div style={{fontSize:'12px', color:'var(--neutral-600)'}}>Huissier de Justice - Parakou</div>
      </div>
      <div style={{textAlign:'center', marginBottom:'10px'}}>
        <div style={{fontSize:'10px', textTransform:'uppercase', color:'var(--neutral-500)'}}>Référence Dossier</div>
        <div className="dossier-ref">175_1125_MAB</div>
      </div>
      <div className="dossier-parties-box">
        <div className="dossier-party-col">
          <div className="dossier-party-title" style={{color:'var(--primary)'}}>DEMANDEUR / CLIENT</div>
          {dossier.demandeurs && dossier.demandeurs.map((d, i) => (
            <div key={i}>
              <div className="dossier-party-name">{d.typePersonne === 'morale' ? d.denomination : `${d.nom || ''} ${d.prenoms || ''}`}</div>
              <div style={{fontSize:'11px'}}>{d.telephone}</div>
              <div style={{fontSize:'11px', color:'var(--neutral-500)'}}>{d.domicile || d.siegeSocial}</div>
            </div>
          ))}
        </div>
        <div className="dossier-party-col">
          <div className="dossier-party-title" style={{color:'var(--accent-dark)'}}>DÉFENDEUR / ADVERSAIRE</div>
          {dossier.isContentieux && dossier.defendeurs ? dossier.defendeurs.map((d, i) => (
            <div key={i}>
              <div className="dossier-party-name">{d.typePersonne === 'morale' ? d.denomination : `${d.nom || ''} ${d.prenoms || ''}`}</div>
              <div style={{fontSize:'11px'}}>{d.telephone}</div>
              <div style={{fontSize:'11px', color:'var(--neutral-500)'}}>{d.domicile || d.siegeSocial}</div>
            </div>
          )) : <div style={{fontStyle:'italic', color:'var(--neutral-400)', marginTop:'10px'}}>Sans objet</div>}
        </div>
      </div>
      <div className="dossier-details-grid">
        <div className="dossier-detail-item"><span className="dossier-label">NATURE</span><span className="dossier-value">{dossier.isContentieux ? 'Contentieux' : 'Non Contentieux'}</span></div>
        <div className="dossier-detail-item"><span className="dossier-label">TYPE</span><span className="dossier-value" style={{textTransform:'capitalize'}}>{dossier.typeDossier || '-'}</span></div>
        <div className="dossier-detail-item"><span className="dossier-label">MONTANT CRÉANCE</span><span className="dossier-value">{parseInt(dossier.montantCreance || 0).toLocaleString('fr-FR')} FCFA</span></div>
        <div className="dossier-detail-item"><span className="dossier-label">DATE OUVERTURE</span><span className="dossier-value">{new Date().toLocaleDateString('fr-FR')}</span></div>
      </div>
      <div style={{border:'1px dashed var(--neutral-300)', padding:'10px', borderRadius:'6px', marginBottom:'20px', fontSize:'12px'}}><span className="dossier-label">OBJET :</span> {dossier.description || "Aucune description"}</div>
      <div className="dossier-footer"><div><div className="dossier-label">AFFECTÉ À :</div><div style={{fontWeight:'bold'}}>{collaborateur?.nom || 'Non assigné'}</div></div><QRCodeGenerator data={{id:'175_1125_MAB'}} /></div>
    </div>
  );
};

// ============================================
// COMPOSANT: FORMULAIRE PARTIE
// ============================================
const PartieForm = ({ partie, index, type, onUpdate, onRemove, isContentieux }) => {
  const [expanded, setExpanded] = useState(true);
  const [typePersonne, setTypePersonne] = useState(partie.typePersonne || 'physique');
  const handleChange = (field, value) => onUpdate(index, { ...partie, [field]: value });
  const roleLabel = type === 'demandeur' ? (isContentieux ? 'Demandeur/Créancier' : 'Client/Requérant') : 'Défendeur/Débiteur';

  return (
    <div style={{ border: '1px solid var(--neutral-200)', borderRadius: 'var(--radius-lg)', padding: '16px', marginBottom: '16px', background: 'var(--neutral-50)' }}>
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <div>
          <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: '600', background: typePersonne === 'physique' ? 'var(--info-light)' : 'var(--accent-light)', color: typePersonne === 'physique' ? 'white' : 'var(--primary-dark)' }}>{typePersonne}</span>
          <h4 style={{marginTop:'5px', fontSize: '14px', fontWeight: '600'}}>{roleLabel} #{index + 1}</h4>
        </div>
        <div style={{display:'flex', gap:'5px'}}>
          <button className="btn btn-sm btn-secondary" onClick={() => setExpanded(!expanded)}>{expanded?<ChevronUp size={14}/>:<ChevronDown size={14}/>}</button>
          {index > 0 && <button className="btn btn-sm btn-danger" onClick={() => onRemove(index)}><Trash2 size={12}/></button>}
        </div>
      </div>
      {expanded && (
        <>
          <div className="toggle-group" style={{margin:'12px 0'}}>
            <div className={`toggle-option ${typePersonne === 'physique' ? 'active' : ''}`} onClick={() => { setTypePersonne('physique'); handleChange('typePersonne', 'physique'); }}>Personne physique</div>
            <div className={`toggle-option ${typePersonne === 'morale' ? 'active' : ''}`} onClick={() => { setTypePersonne('morale'); handleChange('typePersonne', 'morale'); }}>Personne morale</div>
          </div>
          <div className="form-grid">
            {typePersonne === 'physique' ? (
              <>
                <div className="form-group"><label className="form-label">Nom <span style={{color:'red'}}>*</span></label><input className="form-input" value={partie.nom || ''} onChange={e => handleChange('nom', e.target.value)} /></div>
                <div className="form-group"><label className="form-label">Prénoms <span style={{color:'red'}}>*</span></label><input className="form-input" value={partie.prenoms || ''} onChange={e => handleChange('prenoms', e.target.value)} /></div>
                <div className="form-group"><label className="form-label">Nationalité <span style={{color:'red'}}>*</span></label><input className="form-input" placeholder="Ex: Béninoise" value={partie.nationalite || ''} onChange={e => handleChange('nationalite', e.target.value)} /></div>
                <div className="form-group"><label className="form-label">Profession</label><input className="form-input" value={partie.profession || ''} onChange={e => handleChange('profession', e.target.value)} /></div>
                <div className="form-group full-width"><label className="form-label">Domicile <span style={{color:'red'}}>*</span></label><input className="form-input" value={partie.domicile || ''} onChange={e => handleChange('domicile', e.target.value)} /></div>
                <div className="form-group"><label className="form-label">Téléphone</label><input className="form-input" value={partie.telephone || ''} onChange={e => handleChange('telephone', e.target.value)} /></div>
                <div className="form-group"><label className="form-label">IFU</label><input className="form-input" value={partie.ifu || ''} onChange={e => handleChange('ifu', e.target.value)} /></div>
              </>
            ) : (
              <>
                 <div className="form-group full-width"><label className="form-label">Dénomination Sociale <span style={{color:'red'}}>*</span></label><input className="form-input" value={partie.denomination || ''} onChange={e => handleChange('denomination', e.target.value)} /></div>
                 <div className="form-group"><label className="form-label">Capital Social <span style={{color:'red'}}>*</span></label><input className="form-input" type="number" placeholder="FCFA" value={partie.capitalSocial || ''} onChange={e => handleChange('capitalSocial', e.target.value)} /></div>
                 <div className="form-group"><label className="form-label">Forme Juridique</label><select className="form-select" value={partie.formeJuridique || 'SARL'} onChange={e => handleChange('formeJuridique', e.target.value)}><option>SARL</option><option>SA</option><option>SAS</option></select></div>
                 <div className="form-group full-width"><label className="form-label">Siège Social <span style={{color:'red'}}>*</span></label><input className="form-input" value={partie.siegeSocial || ''} onChange={e => handleChange('siegeSocial', e.target.value)} /></div>
                 <div className="form-group"><label className="form-label">Représentant Légal</label><input className="form-input" value={partie.representant || ''} onChange={e => handleChange('representant', e.target.value)} /></div>
                 <div className="form-group"><label className="form-label">IFU <span style={{color:'red'}}>*</span></label><input className="form-input" value={partie.ifu || ''} onChange={e => handleChange('ifu', e.target.value)} /></div>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
};

// ============================================
// MODULE: NOUVEAU DOSSIER (Assistant Complet)
// ============================================
const NouveauDossierModal = ({ onClose }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const steps = ['Type & Affectation', 'Demandeur(s)', 'Défendeur(s)', 'Documents', 'Récapitulatif', 'Impression'];
  const [formData, setFormData] = useState({
    isContentieux: false, typeDossier: '', affecteA: '', description: '', montantCreance: '', dateCreance: '',
    demandeurs: [{ typePersonne: 'physique' }], defendeurs: [{ typePersonne: 'physique' }],
  });

  const handleChange = (field, value) => setFormData(prev => ({ ...prev, [field]: value }));
  const updatePartie = (key, idx, val) => { const arr = [...formData[key]]; arr[idx] = val; handleChange(key, arr); };
  const addPartie = (key) => handleChange(key, [...formData[key], { typePersonne: 'physique' }]);
  const removePartie = (key, idx) => handleChange(key, formData[key].filter((_, i) => i !== idx));
  const genererReference = () => { const now = new Date(); return `175_${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getFullYear()).slice(-2)}_MAB`; };
  const genererNomDossier = () => { const dem = formData.demandeurs[0]?.nom || 'Client'; const def = formData.defendeurs[0]?.nom || 'Adversaire'; return formData.isContentieux ? `${dem} C/ ${def}` : dem; };

  return (
    <div className="modal-overlay">
      <div className="modal large">
        <div className="modal-header"><h2 className="modal-title">Création d'un nouveau dossier</h2><button className="modal-close" onClick={onClose}><X size={20}/></button></div>
        <div className="modal-body">
          <ProgressBar label="Progression" percent={Math.round(((currentStep + 1) / steps.length) * 100)} />
          <Stepper steps={steps} currentStep={currentStep} />
          {currentStep === 0 && (
            <div className="form-grid">
              <div className="form-group full-width"><label className="form-label">Nature</label><div className="toggle-group"><div className={`toggle-option ${!formData.isContentieux ? 'active' : ''}`} onClick={() => handleChange('isContentieux', false)}>Non contentieux</div><div className={`toggle-option ${formData.isContentieux ? 'active' : ''}`} onClick={() => handleChange('isContentieux', true)}>Contentieux</div></div></div>
              <div className="form-group"><label className="form-label">Affecté à <span style={{color:'red'}}>*</span></label><select className="form-select" value={formData.affecteA} onChange={e => handleChange('affecteA', e.target.value)}><option value="">Sélectionner...</option>{COLLABORATEURS.map(c => <option key={c.id} value={c.id}>{c.nom}</option>)}</select></div>
              <div className="form-group"><label className="form-label">Type</label><select className="form-select" value={formData.typeDossier} onChange={e => handleChange('typeDossier', e.target.value)}><option value="">Sélectionner...</option><option value="recouvrement">Recouvrement</option><option value="expulsion">Expulsion</option></select></div>
              <div className="form-group full-width"><label className="form-label">Description</label><textarea className="form-textarea" rows={3} value={formData.description} onChange={e => handleChange('description', e.target.value)} /></div>
            </div>
          )}
          {currentStep === 1 && (<div><Alert type="info">Renseignez le(s) demandeur(s).</Alert>{formData.demandeurs.map((p, i) => <PartieForm key={i} index={i} partie={p} type="demandeur" onUpdate={(idx, data) => updatePartie('demandeurs', idx, data)} onRemove={(idx) => removePartie('demandeurs', idx)} isContentieux={formData.isContentieux} />)}<button className="btn btn-secondary" onClick={() => addPartie('demandeurs')}><Plus size={16}/> Ajouter</button></div>)}
          {currentStep === 2 && (<div>{formData.isContentieux ? (<>{formData.defendeurs.map((p, i) => <PartieForm key={i} index={i} partie={p} type="defendeur" onUpdate={(idx, data) => updatePartie('defendeurs', idx, data)} onRemove={(idx) => removePartie('defendeurs', idx)} isContentieux={formData.isContentieux} />)}<button className="btn btn-secondary" onClick={() => addPartie('defendeurs')}><Plus size={16}/> Ajouter</button></>) : (<div style={{textAlign:'center', padding:'40px'}}><p>Pas de partie adverse pour ce type de dossier.</p></div>)}</div>)}
          {currentStep === 3 && (<div><Alert type="info">Structure automatique Drive générée.</Alert><div style={{ background: 'var(--neutral-50)', padding: '20px', borderRadius: 'var(--radius-lg)' }}>📂 DOSSIERS 2025 / {genererNomDossier()}</div></div>)}
          {currentStep === 4 && (
            <div>
               <div style={{ background: 'linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%)', color: 'white', padding: '24px', borderRadius: 'var(--radius-lg)', marginBottom: '24px' }}>
                 <div style={{ fontSize: '12px', opacity: 0.8, marginBottom: '8px' }}>RÉFÉRENCE DU DOSSIER</div>
                 <div style={{ fontSize: '24px', fontWeight: 700, marginBottom: '16px' }}>{genererReference()}</div>
                 <div style={{ fontSize: '14px' }}>{genererNomDossier()}</div>
               </div>
               <div className="form-grid">
                 <div className="card" style={{ gridColumn: '1 / -1' }}>
                   <div className="card-header"><h4 className="card-title">Informations générales</h4></div>
                   <div className="card-body">
                     <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                       <div><span style={{ color: 'var(--neutral-500)', fontSize: '12px' }}>Nature</span><p style={{ fontWeight: 500 }}>{formData.isContentieux ? 'Contentieux' : 'Non contentieux'}</p></div>
                       <div><span style={{ color: 'var(--neutral-500)', fontSize: '12px' }}>Type</span><p style={{ fontWeight: 500 }}>{formData.typeDossier || '-'}</p></div>
                       <div><span style={{ color: 'var(--neutral-500)', fontSize: '12px' }}>Montant créance</span><p style={{ fontWeight: 500 }}>{formData.montantCreance ? `${parseInt(formData.montantCreance).toLocaleString('fr-FR')} FCFA` : '-'}</p></div>
                       <div><span style={{ color: 'var(--neutral-500)', fontSize: '12px' }}>Affecté à</span><p style={{ fontWeight: 500 }}>{COLLABORATEURS.find(c => c.id == formData.affecteA)?.nom || '-'}</p></div>
                     </div>
                   </div>
                 </div>
               </div>
            </div>
          )}
          {currentStep === 5 && (<div><Alert type="success">Dossier créé !</Alert><div style={{display:'flex', justifyContent:'center', marginTop:'20px'}}><DossierPhysicalCard dossier={formData} collaborateur={COLLABORATEURS.find(c => c.id == formData.affecteA)} /></div></div>)}
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={() => setCurrentStep(Math.max(0, currentStep - 1))} disabled={currentStep===0}>Précédent</button>
          <button className="btn btn-primary" onClick={() => { if (currentStep < steps.length - 1) setCurrentStep(currentStep + 1); else onClose(); }}>{currentStep === 5 ? 'Terminer' : 'Suivant'}</button>
        </div>
      </div>
    </div>
  );
};

// ============================================
// MODULE: FACTURATION
// ============================================
const FacturationModule = () => {
  const [activeTab, setActiveTab] = useState('liste');
  const [showNewInvoice, setShowNewInvoice] = useState(false);
  
  const factures = [
    { id: 'FAC-2025-001', client: 'SODECO SA', montantHT: 150000, tva: 27000, total: 177000, date: '15/11/2025', statut: 'payee' },
    { id: 'FAC-2025-002', client: 'SOGEMA Sarl', montantHT: 85000, tva: 15300, total: 100300, date: '18/11/2025', statut: 'attente' },
    { id: 'FAC-2025-003', client: 'Banque Atlantique', montantHT: 250000, tva: 45000, total: 295000, date: '20/11/2025', statut: 'attente' },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div className="tabs" style={{ marginBottom: 0, borderBottom: 'none' }}>
          <button className={`tab ${activeTab === 'liste' ? 'active' : ''}`} onClick={() => setActiveTab('liste')}>Liste des factures</button>
          <button className={`tab ${activeTab === 'memoires' ? 'active' : ''}`} onClick={() => setActiveTab('memoires')}>Mémoires</button>
          <button className={`tab ${activeTab === 'mecef' ? 'active' : ''}`} onClick={() => setActiveTab('mecef')}>MECeF</button>
        </div>
        <button className="btn btn-primary" onClick={() => setShowNewInvoice(true)}><Plus size={16} /> Nouvelle facture</button>
      </div>
      
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Factures récentes</h3>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn btn-secondary btn-sm"><Filter size={14} /> Filtrer</button>
            <button className="btn btn-secondary btn-sm"><Download size={14} /> Exporter</button>
          </div>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>N° Facture</th>
                <th>Client</th>
                <th>Montant HT</th>
                <th>TVA</th>
                <th>Total TTC</th>
                <th>Date</th>
                <th>Statut</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {factures.map((f, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600, color: 'var(--primary)' }}>{f.id}</td>
                  <td>{f.client}</td>
                  <td>{f.montantHT.toLocaleString('fr-FR')} F</td>
                  <td>{f.tva.toLocaleString('fr-FR')} F</td>
                  <td style={{ fontWeight: 600 }}>{f.total.toLocaleString('fr-FR')} F</td>
                  <td>{f.date}</td>
                  <td>
                    <span className={`status-badge ${f.statut === 'payee' ? 'active' : 'urgent'}`}>
                      {f.statut === 'payee' ? 'Payée' : 'En attente'}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <button className="icon-btn" title="Voir"><Eye size={14} /></button>
                      <button className="icon-btn" title="Imprimer"><Printer size={14} /></button>
                      <button className="icon-btn" title="MECeF"><QrCode size={14} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// ============================================
// MODULE: CALCUL RECOUVREMENT (OHADA PRO)
// ============================================
const CalculRecouvrementModule = () => {
  const [modeCalcul, setModeCalcul] = useState('complet');
  const [currentStep, setCurrentStep] = useState(1);
  const [montantPrincipal, setMontantPrincipal] = useState('');
  const [tauxInteret, setTauxInteret] = useState('');
  const [typeTaux, setTypeTaux] = useState('legal'); 
  const [dateCreance, setDateCreance] = useState('');
  const [dateSaisie, setDateSaisie] = useState('');
  const [typeCalcul, setTypeCalcul] = useState('simple'); 
  const [appliquerMajoration, setAppliquerMajoration] = useState(false);
  const [dateDecisionJustice, setDateDecisionJustice] = useState('');
  const [calculerEmoluments, setCalculerEmoluments] = useState(false);
  const [baseEmoluments, setBaseEmoluments] = useState('');
  const [typeTitreExecutoire, setTypeTitreExecutoire] = useState('sans'); 
  const [fraisJustice, setFraisJustice] = useState('');
  const [calculerActesProcedure, setCalculerActesProcedure] = useState(false);
  const [actesProcedure, setActesProcedure] = useState([]);
  const [nouvelActe, setNouvelActe] = useState({ intitule: '', montant: '' });
  const [resultats, setResultats] = useState(null);
  const [arrondirMontants, setArrondirMontants] = useState(true);
  const [historique, setHistorique] = useState([]);
  const [showHistorique, setShowHistorique] = useState(false);
  const [nomCalcul, setNomCalcul] = useState('');

  const tauxLegauxUEMOA = {
    2010: 6.4800, 2011: 6.2500, 2012: 4.2500, 2013: 4.1141, 2014: 3.7274,
    2015: 3.5000, 2016: 3.5000, 2017: 3.5437, 2018: 4.5000, 2019: 4.5000,
    2020: 4.5000, 2021: 4.2391, 2022: 4.0000, 2023: 4.2205, 2024: 5.0336,
    2025: 5.5000
  };

  const estAnneeBissextile = (annee) => (annee % 4 === 0 && annee % 100 !== 0) || (annee % 400 === 0);
  const obtenirNombreJoursAnnee = (annee) => estAnneeBissextile(annee) ? 366 : 365;
  const obtenirTauxLegal = (date) => {
    const annee = new Date(date).getFullYear();
    return tauxLegauxUEMOA[annee] || 5.5;
  };
  const formatMontant = (m) => {
    if (!m && m !== 0) return '0 FCFA';
    const num = arrondirMontants ? Math.round(m) : m;
    return num.toLocaleString('fr-FR') + ' FCFA';
  };

  const handleAddActe = () => {
    if (nouvelActe.intitule && nouvelActe.montant) {
      setActesProcedure([...actesProcedure, { ...nouvelActe, actif: true, id: Date.now() }]);
      setNouvelActe({ intitule: '', montant: '' });
    }
  };

  const handleSelectActe = (e) => {
    const selectedId = e.target.value;
    const acteCatalogue = CATALOGUE_ACTES.find(a => a.id === selectedId);
    if (acteCatalogue) {
      setNouvelActe({ intitule: acteCatalogue.label, montant: acteCatalogue.tarif });
    }
  };

  const removeActe = (id) => {
    setActesProcedure(actesProcedure.filter(a => a.id !== id));
  };

  const totalActesMontant = actesProcedure.reduce((sum, acte) => sum + (parseFloat(acte.montant) || 0), 0);

  const calculerEmolumentsProportionnels = (base) => {
    const baremes = {
      sans: [{min:1,max:5000000,taux:10}, {min:5000001,max:20000000,taux:8}, {min:20000001,max:50000000,taux:6}, {min:50000001,max:Infinity,taux:4}],
      avec: [{min:1,max:5000000,taux:10}, {min:5000001,max:20000000,taux:3.5}, {min:20000001,max:50000000,taux:2}, {min:50000001,max:Infinity,taux:1}]
    };
    let restant = base, total = 0, cumul = 0;
    
    baremes[typeTitreExecutoire].forEach(t => {
      if(restant <= 0) return;
      const part = Math.min(restant, t.max - cumul);
      if(part > 0) {
        const em = (part * t.taux) / 100;
        total += em;
        restant -= part;
        cumul += part;
      }
    });
    return { total: arrondirMontants ? Math.round(total) : total };
  };

  const calculerInteretsParPeriode = (montant, debut, fin, majore) => {
    let current = new Date(debut);
    const end = new Date(fin);
    let total = 0, periodes = [];

    while(current <= end) {
      const annee = current.getFullYear();
      const finAnnee = new Date(annee, 11, 31);
      const borne = finAnnee < end ? finAnnee : end;
      const jours = Math.floor((borne - current) / (86400000)) + 1;
      
      let taux = typeTaux === 'legal' ? obtenirTauxLegal(current) : parseFloat(tauxInteret || 0);
      if(typeTaux === 'cima') taux = 5 * 12;
      if(majore) taux *= 1.5;

      let interet = typeCalcul === 'simple' 
        ? (montant * taux * jours) / (100 * obtenirNombreJoursAnnee(annee))
        : montant * (Math.pow(1 + taux/100, jours/obtenirNombreJoursAnnee(annee)) - 1);

      periodes.push({ annee, debut: current.toLocaleDateString('fr-FR'), fin: borne.toLocaleDateString('fr-FR'), jours, taux, interet });
      total += interet;
      current = new Date(annee + 1, 0, 1);
    }
    return { periodes, total: arrondirMontants ? Math.round(total) : total };
  };

  const effectuerCalcul = () => {
    if(modeCalcul === 'emoluments') {
      if(!baseEmoluments) return alert('Saisir une base');
      const base = parseFloat(baseEmoluments);
      const emols = calculerEmolumentsProportionnels(base);
      setResultats({ mode: 'emoluments', base, emols, total: base + emols.total });
    } else {
      if(!montantPrincipal || !dateCreance || !dateSaisie) return alert('Champs obligatoires manquants');
      const princ = parseFloat(montantPrincipal);
      const d1 = new Date(dateCreance); d1.setDate(d1.getDate() + 1);
      const d2 = new Date(dateSaisie);
      
      let dateMaj = null;
      if(appliquerMajoration && dateDecisionJustice) {
        const d = new Date(dateDecisionJustice); d.setMonth(d.getMonth() + 2);
        if(d2 > d) dateMaj = d;
      }

      let resEchus;
      if(dateMaj && dateMaj < d2) {
        const p1 = calculerInteretsParPeriode(princ, d1, dateMaj, false);
        const dMajStart = new Date(dateMaj); dMajStart.setDate(dMajStart.getDate() + 1);
        const p2 = calculerInteretsParPeriode(princ, dMajStart, d2, true);
        resEchus = { periodes: [...p1.periodes, ...p2.periodes], total: p1.total + p2.total };
      } else {
        resEchus = calculerInteretsParPeriode(princ, d1, d2, false);
      }

      const d3 = new Date(d2); d3.setDate(d3.getDate() + 1);
      const d4 = new Date(d3); d4.setMonth(d4.getMonth() + 1);
      const resEchoir = calculerInteretsParPeriode(princ, d3, d4, appliquerMajoration && dateMaj);

      let emols = null;
      let baseEmol = princ + resEchus.total;
      if(calculerEmoluments) {
        if(fraisJustice) baseEmol += parseFloat(fraisJustice);
        emols = calculerEmolumentsProportionnels(baseEmol);
      }

      setResultats({
        mode: 'complet',
        principal: princ,
        interetsEchus: resEchus,
        interetsEchoir: resEchoir,
        emoluments: emols,
        baseEmoluments: baseEmol,
        fraisJustice: parseFloat(fraisJustice||0),
        actes: totalActesMontant,
        total: princ + resEchus.total + (fraisJustice?parseFloat(fraisJustice):0) + (emols?emols.total:0) + totalActesMontant,
        dateDebut: d1.toLocaleDateString('fr-FR'),
        dateFin: d2.toLocaleDateString('fr-FR'),
        majoration: appliquerMajoration,
        dateLimiteMajoration: dateMaj ? dateMaj.toLocaleDateString('fr-FR') : null
      });
    }
  };

  const genererTexteActe = () => {
    if (!resultats) return '';
    if (resultats.mode === 'emoluments') return `Calcul d'émoluments:\nBase: ${formatMontant(resultats.base)}\nTotal: ${formatMontant(resultats.total)}`;
    
    let texte = `MENTION JURIDIQUE OHADA (v2.0):\n\n`;
    texte += `PRINCIPAL: ${formatMontant(resultats.principal)}\n`;
    texte += `INTÉRÊTS ÉCHUS (du ${resultats.dateDebut} au ${resultats.dateFin}): ${formatMontant(resultats.interetsEchus.total)}\n`;
    resultats.interetsEchus.periodes.forEach(p => {
      texte += `  - ${p.annee} (${p.jours}j à ${p.taux.toFixed(2)}%): ${formatMontant(p.interet)}\n`;
    });
    
    if (resultats.majoration) {
       texte += `\n⚠️ MAJORATION APPLIQUÉE (+50%) après le ${resultats.dateLimiteMajoration}\n`;
    }

    texte += `\nINTÉRÊTS À ÉCHOIR (1 mois): ${formatMontant(resultats.interetsEchoir.total)}\n`;
    
    if (resultats.emoluments) {
      texte += `\nÉMOLUMENTS PROPORTIONNELS (Base ${formatMontant(resultats.baseEmoluments)}): ${formatMontant(resultats.emoluments.total)}\n`;
    }

    if (resultats.actes > 0) {
        texte += `\nCOÛT DES ACTES DE PROCÉDURE: ${formatMontant(resultats.actes)}\n`;
        actesProcedure.forEach(a => {
            texte += ` - ${a.intitule} : ${formatMontant(parseFloat(a.montant))}\n`;
        });
    }
    
    texte += `\nTOTAL GÉNÉRAL: ${formatMontant(resultats.total)}`;
    return texte;
  };

  const saveCalcul = () => {
    if(!resultats) return;
    const nom = nomCalcul || `Calcul du ${new Date().toLocaleString()}`;
    const save = { id: Date.now(), nom, date: new Date().toLocaleString(), resultats };
    setHistorique([save, ...historique]);
    setNomCalcul('');
    alert('Calcul sauvegardé');
  };

  const canGoNext = () => {
    if (currentStep === 1) return montantPrincipal && parseFloat(montantPrincipal) > 0;
    if (currentStep === 2) return true; 
    if (currentStep === 3) return dateCreance && dateSaisie;
    return true;
  };

  return (
    <div className="space-y-6">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div className="toggle-group">
          <div className={`toggle-option ${modeCalcul==='complet'?'active':''}`} onClick={()=>{setModeCalcul('complet');setCurrentStep(1)}}>Calcul Complet</div>
          <div className={`toggle-option ${modeCalcul==='emoluments'?'active':''}`} onClick={()=>setModeCalcul('emoluments')}>Émoluments Seuls</div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary btn-sm" onClick={()=>setShowHistorique(!showHistorique)}><History size={16}/> Historique</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        <div className="card">
          <div className="card-header"><h3 className="card-title">Paramètres</h3></div>
          <div className="card-body">
            {modeCalcul === 'complet' ? (
              <>
                <Stepper steps={['Principal', 'Taux', 'Dates', 'Options']} currentStep={currentStep - 1} />
                
                {currentStep === 1 && (
                  <div className="form-group">
                    <label className="form-label">Montant principal</label>
                    <input className="form-input" type="number" value={montantPrincipal} onChange={e=>setMontantPrincipal(e.target.value)} placeholder="Ex: 1000000" />
                  </div>
                )}

                {currentStep === 2 && (
                  <div className="space-y-4">
                    <div className="form-group">
                      <label className="form-label">Type de Taux</label>
                      <select className="form-select" value={typeTaux} onChange={e=>setTypeTaux(e.target.value)}>
                        <option value="legal">Légal (UEMOA)</option>
                        <option value="cima">CIMA (Assurance)</option>
                        <option value="conventionnel">Conventionnel</option>
                      </select>
                    </div>
                    {typeTaux === 'conventionnel' && (
                      <div className="form-group"><label className="form-label">Taux (%)</label><input className="form-input" type="number" value={tauxInteret} onChange={e=>setTauxInteret(e.target.value)} /></div>
                    )}
                  </div>
                )}

                {currentStep === 3 && (
                  <div className="space-y-4">
                    <div className="form-grid">
                      <div className="form-group"><label className="form-label">Date Créance (Dies a quo)</label><input className="form-input" type="date" value={dateCreance} onChange={e=>setDateCreance(e.target.value)} /></div>
                      <div className="form-group"><label className="form-label">Date Saisie (Dies ad quem)</label><input className="form-input" type="date" value={dateSaisie} onChange={e=>setDateSaisie(e.target.value)} /></div>
                    </div>
                    <div style={{ background: 'rgba(237, 137, 54, 0.1)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(237, 137, 54, 0.3)' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px', fontWeight: '500', color: 'var(--warning)' }}>
                        <input type="checkbox" checked={appliquerMajoration} onChange={e=>setAppliquerMajoration(e.target.checked)}/>
                        Appliquer Majoration (Loi 2024)
                      </label>
                      {appliquerMajoration && <input className="form-input" style={{ marginTop: '8px' }} type="date" value={dateDecisionJustice} onChange={e=>setDateDecisionJustice(e.target.value)} />}
                    </div>
                  </div>
                )}

                {currentStep === 4 && (
                  <div className="space-y-4">
                    <div className="form-group">
                      <label className="form-label">Type Calcul</label>
                      <select className="form-select" value={typeCalcul} onChange={e=>setTypeCalcul(e.target.value)}>
                        <option value="simple">Intérêts Simples</option>
                        <option value="compose">Intérêts Composés</option>
                      </select>
                    </div>
                    <div style={{ borderTop: '1px solid var(--neutral-200)', paddingTop: '16px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', fontWeight: '600', fontSize: '13px' }}>
                        <input type="checkbox" checked={calculerEmoluments} onChange={e=>setCalculerEmoluments(e.target.checked)}/>
                        Ajouter Émoluments
                      </label>
                      {calculerEmoluments && (
                        <div style={{ paddingLeft: '16px', borderLeft: '2px solid var(--neutral-200)' }}>
                          <div className="form-group" style={{ marginTop: '8px' }}>
                            <label className="form-label">Titre Exécutoire</label>
                            <select className="form-select" value={typeTitreExecutoire} onChange={e=>setTypeTitreExecutoire(e.target.value)}>
                              <option value="sans">Sans titre</option>
                              <option value="avec">Avec titre</option>
                            </select>
                          </div>
                          <div className="form-group" style={{ marginTop: '8px' }}>
                            <label className="form-label">Frais de Justice</label>
                            <input className="form-input" type="number" value={fraisJustice} onChange={e=>setFraisJustice(e.target.value)}/>
                          </div>
                          
                          <div className="form-group" style={{ marginTop: '12px' }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                              <input type="checkbox" checked={calculerActesProcedure} onChange={e=>setCalculerActesProcedure(e.target.checked)}/>
                              Coûts des actes de procédure
                            </label>
                            {calculerActesProcedure && (
                              <div style={{ marginTop: '8px', background: 'var(--neutral-50)', padding: '12px', borderRadius: '8px', border: '1px solid var(--neutral-200)' }}>
                                {actesProcedure.length > 0 && (
                                  <div style={{ marginBottom: '12px' }}>
                                    {actesProcedure.map((acte) => (
                                      <div key={acte.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid var(--neutral-200)' }}>
                                        <span style={{ fontSize: '12px' }}>{acte.intitule}</span>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                          <span style={{ fontSize: '12px', fontWeight: '600' }}>{formatMontant(parseInt(acte.montant))}</span>
                                          <button onClick={() => removeActe(acte.id)} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}><Trash2 size={12}/></button>
                                        </div>
                                      </div>
                                    ))}
                                    <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '8px', fontWeight: '700', fontSize: '13px' }}>
                                      <span>TOTAL</span>
                                      <span style={{ color: 'var(--primary)' }}>{formatMontant(totalActesMontant)}</span>
                                    </div>
                                  </div>
                                )}
                                <select className="form-select" style={{ fontSize: '12px', marginBottom: '8px' }} onChange={handleSelectActe} defaultValue="">
                                  <option value="">-- Catalogue --</option>
                                  {CATALOGUE_ACTES.map(a => <option key={a.id} value={a.id}>{a.label}</option>)}
                                </select>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                  <input className="form-input" style={{ flex: 1, fontSize: '12px' }} placeholder="Libellé" value={nouvelActe.intitule} onChange={e => setNouvelActe({...nouvelActe, intitule: e.target.value})} />
                                  <input className="form-input" style={{ width: '80px', fontSize: '12px' }} type="number" placeholder="Coût" value={nouvelActe.montant} onChange={e => setNouvelActe({...nouvelActe, montant: e.target.value})} />
                                </div>
                                <button className="btn btn-sm btn-secondary" style={{ width: '100%', marginTop: '8px' }} onClick={handleAddActe}><Plus size={12}/> Ajouter</button>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div style={{ display: 'flex', gap: '8px', marginTop: '24px' }}>
                  {currentStep > 1 && <button className="btn btn-secondary" style={{ flex: 1 }} onClick={()=>setCurrentStep(currentStep-1)}>Précédent</button>}
                  {currentStep < 4 ? (
                    <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => canGoNext() && setCurrentStep(currentStep+1)}>Suivant</button>
                  ) : (
                    <button className="btn btn-success" style={{ flex: 1 }} onClick={effectuerCalcul}>Calculer</button>
                  )}
                </div>
              </>
            ) : (
              <div className="space-y-4">
                <div className="form-group"><label className="form-label">Base Calcul</label><input className="form-input" type="number" value={baseEmoluments} onChange={e=>setBaseEmoluments(e.target.value)} /></div>
                <div className="form-group"><label className="form-label">Titre</label><select className="form-select" value={typeTitreExecutoire} onChange={e=>setTypeTitreExecutoire(e.target.value)}><option value="sans">Sans titre</option><option value="avec">Avec titre</option></select></div>
                <button className="btn btn-primary" style={{ width: '100%', marginTop: '16px' }} onClick={effectuerCalcul}>Calculer</button>
              </div>
            )}
          </div>
        </div>

        <div>
          {resultats ? (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Résultats</h3>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input className="form-input" style={{ padding: '6px 10px', width: '150px' }} placeholder="Nom sauvegarde" value={nomCalcul} onChange={e=>setNomCalcul(e.target.value)} />
                  <button className="btn btn-secondary btn-sm" onClick={saveCalcul}><Save size={14}/> Sauvegarder</button>
                  <button className="btn btn-accent btn-sm" onClick={()=>navigator.clipboard.writeText(genererTexteActe())}><Copy size={14}/> Copier</button>
                </div>
              </div>
              <div className="card-body">
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
                  <div style={{ padding: '12px', background: 'rgba(43, 108, 176, 0.1)', borderRadius: '8px', textAlign: 'center' }}>
                    <div style={{ fontSize: '10px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--info)' }}>Principal</div>
                    <div style={{ fontSize: '18px', fontWeight: '700', color: 'var(--primary)' }}>{formatMontant(resultats.mode==='emoluments'?resultats.base:resultats.principal)}</div>
                  </div>
                  {resultats.mode === 'complet' && (
                    <div style={{ padding: '12px', background: 'rgba(47, 133, 90, 0.1)', borderRadius: '8px', textAlign: 'center' }}>
                      <div style={{ fontSize: '10px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--success)' }}>Intérêts</div>
                      <div style={{ fontSize: '18px', fontWeight: '700', color: 'var(--success)' }}>{formatMontant(resultats.interetsEchus.total)}</div>
                    </div>
                  )}
                  {resultats.emoluments && (
                    <div style={{ padding: '12px', background: 'rgba(128, 90, 213, 0.1)', borderRadius: '8px', textAlign: 'center' }}>
                      <div style={{ fontSize: '10px', fontWeight: '700', textTransform: 'uppercase', color: '#805ad5' }}>Émoluments</div>
                      <div style={{ fontSize: '18px', fontWeight: '700', color: '#805ad5' }}>{formatMontant(resultats.emoluments.total)}</div>
                    </div>
                  )}
                  <div style={{ padding: '12px', background: 'var(--primary)', borderRadius: '8px', textAlign: 'center' }}>
                    <div style={{ fontSize: '10px', fontWeight: '700', textTransform: 'uppercase', color: 'rgba(255,255,255,0.7)' }}>TOTAL</div>
                    <div style={{ fontSize: '18px', fontWeight: '700', color: 'white' }}>{formatMontant(resultats.total)}</div>
                  </div>
                </div>

                <div style={{ background: 'white', border: '1px solid var(--neutral-200)', borderRadius: '8px', padding: '16px', fontFamily: 'monospace', fontSize: '12px', lineHeight: '1.8', whiteSpace: 'pre-wrap', maxHeight: '400px', overflowY: 'auto' }}>
                  {genererTexteActe()}
                </div>
              </div>
            </div>
          ) : (
            <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--neutral-50)', border: '2px dashed var(--neutral-200)' }}>
              <div style={{ textAlign: 'center', color: 'var(--neutral-400)', padding: '40px' }}>
                <Calculator size={48} style={{ marginBottom: '16px', opacity: 0.5 }}/>
                <p>Configurez les paramètres et lancez le calcul</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {showHistorique && (
        <div className="modal-overlay" onClick={()=>setShowHistorique(false)}>
          <div className="modal" onClick={e=>e.stopPropagation()}>
            <div className="modal-header"><h3 className="modal-title">Historique des Calculs</h3><button className="modal-close" onClick={()=>setShowHistorique(false)}><X size={20}/></button></div>
            <div className="modal-body">
              {historique.length === 0 ? <p style={{ textAlign: 'center', color: 'var(--neutral-500)' }}>Aucun historique.</p> : (
                <table style={{ width: '100%' }}>
                  <thead><tr><th>Nom</th><th>Date</th><th>Total</th></tr></thead>
                  <tbody>
                    {historique.map((h, i) => (
                      <tr key={i}>
                        <td style={{ fontWeight: '500' }}>{h.nom}</td>
                        <td style={{ color: 'var(--neutral-500)' }}>{h.date}</td>
                        <td style={{ fontWeight: '700' }}>{formatMontant(h.resultats.total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================
// MODULE: DOSSIERS
// ============================================
const DossiersModule = ({ onOpenModal }) => {
  const [filter, setFilter] = useState({ search: '', type: 'all', assigned: 'all' });
  
  const handleDelete = () => { 
    if (CURRENT_USER.role !== 'admin') { 
      alert("Action non autorisée : Seul l'administrateur peut supprimer un dossier."); 
      return; 
    } 
    if(window.confirm("Confirmer la suppression définitive de ce dossier ?")) { 
      console.log("Dossier supprimé"); 
    } 
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div className="tabs" style={{ marginBottom: 0, borderBottom: 'none' }}>
          <button className="tab active">Tous (127)</button>
          <button className="tab">Actifs (89)</button>
          <button className="tab">Urgents (14)</button>
          <button className="tab">Archivés (24)</button>
        </div>
        <button className="btn btn-primary" onClick={() => onOpenModal('nouveau-dossier')}><Plus size={16} /> Nouveau dossier</button>
      </div>
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', gap: '10px', flex: 1, flexWrap:'wrap' }}>
            <div className="search-bar" style={{ maxWidth: '300px' }}><Search /><input type="text" placeholder="Rechercher..." value={filter.search} onChange={e => setFilter({...filter, search: e.target.value})} /></div>
            <select className="form-select" style={{width: '180px'}} value={filter.type} onChange={e => setFilter({...filter, type: e.target.value})}>
              <option value="all">Tous types</option>
              <option value="recouvrement">Recouvrement</option>
              <option value="constat">Constat</option>
              <option value="expulsion">Expulsion</option>
            </select>
            <select className="form-select" style={{width: '180px'}} value={filter.assigned} onChange={e => setFilter({...filter, assigned: e.target.value})}>
              <option value="all">Tous collaborateurs</option>
              {COLLABORATEURS.map(c => <option key={c.id} value={c.id}>{c.nom}</option>)}
            </select>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn btn-secondary btn-sm"><Filter size={14} /> Filtres</button>
            <button className="btn btn-secondary btn-sm"><Download size={14} /> Exporter</button>
          </div>
        </div>
        <div className="table-container">
          <table>
            <thead><tr><th>Référence</th><th>Intitulé / Parties</th><th>Type</th><th>Nature</th><th>Montant</th><th>Affecté à</th><th>Statut</th><th>Actions</th></tr></thead>
            <tbody>
              <tr>
                <td style={{ fontWeight: 600, color: 'var(--primary)' }}>173_1125_MAB</td>
                <td>SODECO SA C/ SOGEMA Sarl</td>
                <td>Recouvrement</td>
                <td><span className="status-badge contentieux">Contentieux</span></td>
                <td>15 750 000 F</td>
                <td>Me BIAOU</td>
                <td><span className="status-badge active"><CheckCircle size={10} /> Actif</span></td>
                <td>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button className="icon-btn" title="Voir"><Eye size={14} /></button>
                    <button className="icon-btn" title="Modifier"><Edit size={14} /></button>
                    <button className="icon-btn" title="QR Code"><QrCode size={14} /></button>
                    <button className="icon-btn" title="Supprimer" style={{color:'var(--danger)'}} onClick={handleDelete}><Trash2 size={14} /></button>
                  </div>
                </td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600, color: 'var(--primary)' }}>174_1125_MAB</td>
                <td>Banque Atlantique C/ TECH SOLUTIONS</td>
                <td>Recouvrement</td>
                <td><span className="status-badge contentieux">Contentieux</span></td>
                <td>8 500 000 F</td>
                <td>ADJOVI Carine</td>
                <td><span className="status-badge urgent"><AlertCircle size={10} /> Urgent</span></td>
                <td>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button className="icon-btn" title="Voir"><Eye size={14} /></button>
                    <button className="icon-btn" title="Modifier"><Edit size={14} /></button>
                    <button className="icon-btn" title="QR Code"><QrCode size={14} /></button>
                    <button className="icon-btn" title="Supprimer" style={{color:'var(--danger)'}} onClick={handleDelete}><Trash2 size={14} /></button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// ============================================
// MODULE: DRIVE (Gestion Documentaire Complète)
// ============================================
const DriveModule = () => {
  const [documents, setDocuments] = useState([]);
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentView, setCurrentView] = useState('grid');
  const [currentFolder, setCurrentFolder] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [showContextMenu, setShowContextMenu] = useState(false);
  const [contextMenuPos, setContextMenuPos] = useState({ x: 0, y: 0 });
  const [stats, setStats] = useState({ total_documents: 0, espace_utilise: 0 });
  const fileInputRef = useRef(null);
  const [showGenModal, setShowGenModal] = useState(null);

  useEffect(() => {
    loadDocuments();
    loadFolders();
    loadStats();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const res = await fetch('/documents/api/documents/');
      const data = await res.json();
      if (data.success) setDocuments(data.documents);
    } catch (e) { console.error('Erreur chargement documents:', e); }
    setLoading(false);
  };

  const loadFolders = async () => {
    try {
      const res = await fetch('/documents/api/dossiers/');
      const data = await res.json();
      if (data.success) setFolders(data.dossiers);
    } catch (e) { console.error('Erreur chargement dossiers:', e); }
  };

  const loadStats = async () => {
    try {
      const res = await fetch('/documents/api/statistiques/');
      const data = await res.json();
      if (data.success) setStats(data.statistiques);
    } catch (e) { console.error('Erreur chargement stats:', e); }
  };

  const handleUpload = async (e) => {
    const files = e.target.files;
    if (!files.length) return;
    const formData = new FormData();
    for (let file of files) formData.append('fichiers', file);
    formData.append('type_document', 'autre');
    try {
      const res = await fetch('/documents/api/documents/upload/', { method: 'POST', body: formData });
      const data = await res.json();
      if (data.success) { loadDocuments(); loadStats(); }
      else alert(data.error || 'Erreur upload');
    } catch (e) { console.error('Erreur upload:', e); }
    e.target.value = '';
  };

  const handleDelete = async (docId) => {
    if (!confirm('Supprimer ce document ?')) return;
    try {
      const res = await fetch('/documents/api/documents/supprimer/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: docId })
      });
      const data = await res.json();
      if (data.success) loadDocuments();
    } catch (e) { console.error('Erreur suppression:', e); }
  };

  const handleShare = async (docId) => {
    const email = prompt('Email du destinataire :');
    if (!email) return;
    try {
      const res = await fetch('/documents/api/partage/creer/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: docId, destinataire_email: email })
      });
      const data = await res.json();
      if (data.success) alert('Lien de partage : ' + window.location.origin + data.partage.lien);
    } catch (e) { console.error('Erreur partage:', e); }
  };

  const handleContextMenu = (e, doc) => {
    e.preventDefault();
    setSelectedDoc(doc);
    setContextMenuPos({ x: e.clientX, y: e.clientY });
    setShowContextMenu(true);
  };

  const getFileIcon = (ext) => {
    const icons = { '.pdf': '📄', '.doc': '📝', '.docx': '📝', '.xls': '📊', '.xlsx': '📊', '.jpg': '🖼️', '.png': '🖼️' };
    return icons[ext] || '📎';
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' o';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' Ko';
    return (bytes / (1024 * 1024)).toFixed(1) + ' Mo';
  };

  const filteredDocs = documents.filter(d =>
    !searchQuery || d.nom.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '24px', minHeight: 'calc(100vh - 150px)' }}>
      {/* Sidebar */}
      <div className="card" style={{ height: 'fit-content' }}>
        <div className="card-header" style={{ flexDirection: 'column', alignItems: 'stretch', gap: '12px' }}>
          <h3 className="card-title">Mes Documents</h3>
          <button className="btn btn-primary w-full" onClick={() => fileInputRef.current?.click()}>
            <Upload size={16} /> Uploader
          </button>
          <input ref={fileInputRef} type="file" multiple hidden onChange={handleUpload} />
        </div>
        <div className="card-body" style={{ padding: '12px' }}>
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--neutral-500)', marginBottom: '8px', fontWeight: '600' }}>Navigation</div>
            {[
              { id: 'all', label: 'Tous les fichiers', icon: Folder, count: documents.length },
              { id: 'recent', label: 'Récents', icon: Clock },
              { id: 'shared', label: 'Partagés', icon: Users },
              { id: 'trash', label: 'Corbeille', icon: Trash2 },
            ].map(item => (
              <div key={item.id} onClick={() => setCurrentFolder(item.id)}
                style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', borderRadius: '8px', cursor: 'pointer',
                  background: currentFolder === item.id ? 'rgba(26, 54, 93, 0.1)' : 'transparent',
                  color: currentFolder === item.id ? 'var(--primary)' : 'var(--neutral-700)' }}>
                <item.icon size={18} style={{ color: 'var(--accent)' }} />
                <span style={{ flex: 1, fontSize: '13px', fontWeight: '500' }}>{item.label}</span>
                {item.count !== undefined && <span style={{ background: 'var(--neutral-200)', padding: '2px 8px', borderRadius: '10px', fontSize: '11px' }}>{item.count}</span>}
              </div>
            ))}
          </div>
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--neutral-500)', marginBottom: '8px', fontWeight: '600' }}>Actions rapides</div>
            {[
              { label: 'Générer fiche dossier', icon: FileText, action: 'fiche' },
              { label: 'Générer acte', icon: FileSignature, action: 'acte' },
              { label: 'Générer lettre', icon: Mail, action: 'lettre' },
            ].map((item, i) => (
              <div key={i} onClick={() => setShowGenModal(item.action)}
                style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', borderRadius: '8px', cursor: 'pointer', color: 'var(--neutral-700)' }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--neutral-100)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                <item.icon size={18} style={{ color: 'var(--accent)' }} />
                <span style={{ fontSize: '13px' }}>{item.label}</span>
              </div>
            ))}
          </div>
          <div style={{ background: 'var(--neutral-100)', padding: '12px', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '12px' }}>
              <span>Espace utilisé</span>
              <span style={{ fontWeight: '600' }}>{formatSize(stats.espace_utilise)}</span>
            </div>
            <div style={{ height: '6px', background: 'var(--neutral-300)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${Math.min((stats.espace_utilise / (5 * 1024 * 1024 * 1024)) * 100, 100)}%`, background: 'linear-gradient(90deg, var(--primary), var(--accent))', borderRadius: '3px' }} />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="card">
        <div className="card-header" style={{ flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
            <div className="search-bar" style={{ maxWidth: '300px' }}>
              <Search size={18} />
              <input placeholder="Rechercher..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <div style={{ display: 'flex', background: 'var(--neutral-100)', borderRadius: '6px', padding: '2px' }}>
              <button className={`btn btn-sm ${currentView === 'grid' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setCurrentView('grid')} style={{ borderRadius: '4px' }}>
                <Layers size={14} />
              </button>
              <button className={`btn btn-sm ${currentView === 'list' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setCurrentView('list')} style={{ borderRadius: '4px' }}>
                <Menu size={14} />
              </button>
            </div>
          </div>
        </div>
        <div className="card-body">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px', color: 'var(--neutral-500)' }}>
              <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite', marginBottom: '16px' }} />
              <p>Chargement...</p>
            </div>
          ) : filteredDocs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px', color: 'var(--neutral-500)' }}>
              <HardDrive size={64} style={{ marginBottom: '16px', opacity: 0.3 }} />
              <h3 style={{ marginBottom: '8px', color: 'var(--neutral-600)' }}>Aucun document</h3>
              <p style={{ fontSize: '14px' }}>Uploadez des fichiers ou générez des documents</p>
              <button className="btn btn-accent" style={{ marginTop: '16px' }} onClick={() => fileInputRef.current?.click()}>
                <Upload size={16} /> Uploader des fichiers
              </button>
            </div>
          ) : currentView === 'grid' ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '16px' }}>
              {filteredDocs.map(doc => (
                <div key={doc.id} onContextMenu={(e) => handleContextMenu(e, doc)}
                  style={{ background: 'white', border: '1px solid var(--neutral-200)', borderRadius: '10px', padding: '16px', cursor: 'pointer', transition: 'all 0.2s' }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--neutral-200)'; e.currentTarget.style.boxShadow = 'none'; }}>
                  <div style={{ height: '80px', background: 'var(--neutral-100)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '36px', marginBottom: '12px' }}>
                    {getFileIcon(doc.extension)}
                  </div>
                  <div style={{ fontSize: '13px', fontWeight: '500', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: '4px' }} title={doc.nom}>{doc.nom}</div>
                  <div style={{ fontSize: '11px', color: 'var(--neutral-500)' }}>{doc.taille_humaine}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr><th>Nom</th><th>Type</th><th>Taille</th><th>Date</th><th>Actions</th></tr>
                </thead>
                <tbody>
                  {filteredDocs.map(doc => (
                    <tr key={doc.id} onContextMenu={(e) => handleContextMenu(e, doc)}>
                      <td style={{ fontWeight: '500' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ fontSize: '20px' }}>{getFileIcon(doc.extension)}</span>
                          {doc.nom}
                        </div>
                      </td>
                      <td>{doc.type_document_display}</td>
                      <td>{doc.taille_humaine}</td>
                      <td>{new Date(doc.date_creation).toLocaleDateString('fr-FR')}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          {doc.url && <a href={doc.url} target="_blank" className="btn btn-sm btn-secondary"><Eye size={12} /></a>}
                          <button className="btn btn-sm btn-secondary" onClick={() => handleShare(doc.id)}><Users size={12} /></button>
                          <button className="btn btn-sm btn-danger" onClick={() => handleDelete(doc.id)}><Trash2 size={12} /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Context Menu */}
      {showContextMenu && (
        <div onClick={() => setShowContextMenu(false)} style={{ position: 'fixed', inset: 0, zIndex: 100 }}>
          <div style={{ position: 'fixed', left: contextMenuPos.x, top: contextMenuPos.y, background: 'white', borderRadius: '8px', boxShadow: '0 4px 20px rgba(0,0,0,0.15)', padding: '8px 0', minWidth: '180px', zIndex: 101 }}
            onClick={e => e.stopPropagation()}>
            {selectedDoc?.url && <div style={{ padding: '10px 16px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px' }}
              onClick={() => { window.open(selectedDoc.url, '_blank'); setShowContextMenu(false); }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--neutral-100)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              <Eye size={16} /> Aperçu
            </div>}
            <div style={{ padding: '10px 16px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px' }}
              onClick={() => { handleShare(selectedDoc?.id); setShowContextMenu(false); }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--neutral-100)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              <Users size={16} /> Partager
            </div>
            <div style={{ height: '1px', background: 'var(--neutral-200)', margin: '8px 0' }} />
            <div style={{ padding: '10px 16px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px', color: 'var(--danger)' }}
              onClick={() => { handleDelete(selectedDoc?.id); setShowContextMenu(false); }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--neutral-100)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              <Trash2 size={16} /> Supprimer
            </div>
          </div>
        </div>
      )}

      {/* Modal Génération */}
      {showGenModal && (
        <div className="modal-overlay" onClick={() => setShowGenModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <div className="modal-header">
              <h2 className="modal-title">
                {showGenModal === 'fiche' && 'Générer fiche dossier'}
                {showGenModal === 'acte' && 'Générer un acte'}
                {showGenModal === 'lettre' && 'Générer une lettre'}
              </h2>
              <button className="modal-close" onClick={() => setShowGenModal(null)}><X size={20} /></button>
            </div>
            <div className="modal-body">
              <Alert type="info">
                Cette fonctionnalité génère automatiquement un document PDF professionnel avec les informations du dossier sélectionné.
              </Alert>
              <div className="form-group" style={{ marginTop: '16px' }}>
                <label className="form-label">Sélectionner le dossier</label>
                <select className="form-select">
                  <option value="">Choisir un dossier...</option>
                  <option value="175_1125_MAB">175_1125_MAB - DUPONT C/ MARTIN</option>
                  <option value="174_1125_MAB">174_1125_MAB - SARL EXAMPLE</option>
                </select>
              </div>
              {showGenModal === 'acte' && (
                <div className="form-group" style={{ marginTop: '16px' }}>
                  <label className="form-label">Type d'acte</label>
                  <select className="form-select">
                    <option value="">Choisir...</option>
                    <option value="commandement">Commandement de payer</option>
                    <option value="signification">Signification de décision</option>
                    <option value="pv_saisie">Procès-verbal de saisie</option>
                    <option value="pv_constat">Procès-verbal de constat</option>
                    <option value="denonciation">Dénonciation</option>
                  </select>
                </div>
              )}
              {showGenModal === 'lettre' && (
                <div className="form-group" style={{ marginTop: '16px' }}>
                  <label className="form-label">Type de lettre</label>
                  <select className="form-select">
                    <option value="">Choisir...</option>
                    <option value="mise_demeure">Mise en demeure</option>
                    <option value="relance">Relance</option>
                    <option value="accuse">Accusé de réception</option>
                  </select>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowGenModal(null)}>Annuler</button>
              <button className="btn btn-primary" onClick={() => { alert('Document généré ! (Connectez le backend pour la génération réelle)'); setShowGenModal(null); }}>
                <FileText size={16} /> Générer
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
};

const SecuriteModule = () => (
  <div className="card">
    <div className="card-header">
      <h3 className="card-title">Gestion des Accès</h3>
      <button className="btn btn-primary btn-sm"><UserPlus size={14} /> Ajouter</button>
    </div>
    <div className="card-body">
      <div className="table-container">
        <table>
          <thead><tr><th>Utilisateur</th><th>Rôle</th><th>Email</th><th>Statut</th><th>Actions</th></tr></thead>
          <tbody>
            {COLLABORATEURS.map(c => (
              <tr key={c.id}>
                <td style={{ fontWeight: '500' }}>{c.nom}</td>
                <td>{c.role}</td>
                <td style={{ color: 'var(--neutral-500)' }}>{c.nom.toLowerCase().replace(' ', '.')}@etude-biaou.bj</td>
                <td><span className="status-badge active">Actif</span></td>
                <td>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button className="icon-btn"><Edit size={14} /></button>
                    <button className="icon-btn"><Key size={14} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

// ============================================
// MODULE: DASHBOARD AVANCÉ
// ============================================
const AdvancedDashboard = ({ onNavigate, onOpenModal }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [lastRefresh, setLastRefresh] = useState(null);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    loadDashboardData();
    const refreshTimer = setInterval(loadDashboardData, 5 * 60 * 1000);
    return () => clearInterval(refreshTimer);
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/dashboard/');
      const json = await res.json();
      if (json.success) { setData(json); setLastRefresh(new Date()); }
    } catch (e) {
      console.error('Erreur chargement dashboard:', e);
      setData(getDefaultData());
    }
    setLoading(false);
  };

  const getDefaultData = () => ({
    kpis: { dossiers_en_cours: 47, solde_tresorerie: 2450000, rdv_aujourdhui: 5, taches_aujourdhui: 8, alertes_urgentes: 3, dossiers_nouveaux_mois: 3, audiences_aujourdhui: 2 },
    dossiers: { en_cours: 47, en_attente: 15, clotures_mois: 10, sans_activite_30j: 5, derniers: [
      { reference: 'DOS-2025-089', type_dossier: 'recouvrement', date_ouverture: '2025-11-25' },
      { reference: 'DOS-2025-088', type_dossier: 'saisie', date_ouverture: '2025-11-24' },
      { reference: 'DOS-2025-087', type_dossier: 'expulsion', date_ouverture: '2025-11-23' },
    ]},
    agenda: { rendez_vous: [
      { heure: '09:00', titre: 'Audience TPI Parakou', type: 'audience', dossier_ref: 'DOS-2025-045' },
      { heure: '11:30', titre: 'RDV Client - M. BOKO', type: 'client', dossier_ref: 'DOS-2025-078' },
      { heure: '14:00', titre: 'Constat urgent - Quartier Zongo', type: 'constat', dossier_ref: 'DOS-2025-089' },
      { heure: '16:00', titre: 'Signification - Me AHOUNOU', type: 'signification', dossier_ref: 'DOS-2025-052' },
    ], taches: [
      { titre: 'Rédiger PV de saisie (DOS-2025-067)', priorite: 'urgent', statut: 'a_faire' },
      { titre: 'Appeler M. SODJI pour relance', priorite: 'normal', statut: 'a_faire' },
      { titre: 'Préparer dossier audience demain', priorite: 'normal', statut: 'a_faire' },
      { titre: 'Envoyer facture Banque ABC', priorite: 'normal', statut: 'termine' },
    ], taches_retard: 2 },
    tresorerie: { caisses: [
      { nom: 'Caisse principale Parakou', solde: 1850000 },
      { nom: 'Caisse secondaire', solde: 600000 },
      { nom: 'Compte séquestre', solde: 2340000 },
    ], total: 4790000, encaissements_jour: { montant: 350000, count: 3 }, decaissements_jour: { montant: 125000, count: 2 }, decaissements_attente: 2 },
    facturation: { emises: { count: 15, total: 2450000 }, payees: { count: 12, total: 1980000 }, attente: { count: 3, total: 470000 }, impayees_30j: [
      { numero: 'FAC-2025-078', montant_ttc: 185000, jours: 45 },
      { numero: 'FAC-2025-065', montant_ttc: 95000, jours: 52 },
    ], taux_recouvrement: 81 },
    comptabilite: { chiffre_affaires: 3250000, charges: 1450000, resultat_net: 1800000, tva_a_declarer: 487500 },
    recouvrement: { amiables: { count: 12, total: 8500000 }, forces: { count: 23, total: 45200000 }, total_creances: 53700000, encaissements_mois: 4850000, reversements_mois: 3920000, emoluments_mois: 485000, taux_recouvrement: 34, reversements_attente: { count: 3, total: 1250000 }, dossiers_sans_activite: 5 },
    gerance: { biens_gestion: 28, biens_loues: 24, biens_vacants: 4, taux_occupation: 86, loyers_attendus: 4200000, loyers_encaisses: 3650000, loyers_impayes: 550000, locataires_impayes: 5, etats_lieux_a_faire: 2, reversements_proprietaires: 2890000, baux_expirent_30j: 1 },
    rh: { effectif_total: 8, presents_aujourdhui: 7, en_conge: 1, absents: 0, conges_en_cours: [{ employe: 'ADJOVI Marie', type: 'Congé annuel', date_fin: '30/11' }], alertes: [
      { type: 'fin_essai', message: 'Fin période essai : KONOU Paul', date: '05/12' },
      { type: 'fin_cdd', message: 'Fin CDD : SAVI Jean', date: '31/12' },
    ]},
    memoires: { attente_paiement: { count: 5, total: 876500 }, payes_mois: { count: 3, total: 542000 }, cedules_en_cours: 12, derniers_paiements: [
      { numero: 82, montant_total: 185000 }, { numero: 81, montant_total: 210000 },
    ], attente_longue: [
      { numero: 78, montant_total: 156000, jours: 73 }, { numero: 76, montant_total: 98500, jours: 87 },
    ]},
    alertes: { urgentes: [
      { message: 'Audience demain 9h - Dossier DOS-2025-045' },
      { message: 'Décaissement 450 000 F en attente approbation' },
      { message: 'Tâche en retard : Signification ordonnance (3 jours)' },
    ], importantes: [
      { message: '3 reversements créanciers à effectuer' },
      { message: '2 reversements propriétaires en attente' },
      { message: 'TVA à déclarer avant le 15/12' },
    ], informations: [
      { message: '5 factures impayées > 30 jours' },
      { message: '4 biens vacants à louer' },
    ]}
  });

  const formatMontant = (m) => {
    if (m >= 1000000) return `${(m / 1000000).toFixed(1)} M F`;
    if (m >= 1000) return `${Math.round(m / 1000)} K F`;
    return `${m.toLocaleString('fr-FR')} F`;
  };

  const formatDate = (d) => d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const formatTime = (d) => d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  const getRdvClass = (t) => ({ audience: 'audience', client: 'client', constat: 'constat' }[t] || '');

  const isAdmin = CURRENT_USER.role === 'admin' || CURRENT_USER.role === 'huissier';
  const greeting = isAdmin ? `Bonjour, Maître ${CURRENT_USER.nom.split(' ')[0]}` : `Bonjour, ${CURRENT_USER.nom.split(' ')[1] || CURRENT_USER.nom}`;

  if (!data) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}><RefreshCw size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--primary)' }} /></div>;

  return (
    <div style={{ paddingBottom: '80px' }}>
      {/* EN-TÊTE */}
      <div className="dashboard-header">
        <div>
          <h1>{greeting}</h1>
          <div style={{ opacity: 0.8, fontSize: '14px', textTransform: 'capitalize' }}>{formatDate(currentTime)}</div>
        </div>
        <div className="datetime">
          <div className="clock">{formatTime(currentTime)}</div>
          <div className="refresh-indicator" style={{ cursor: 'pointer' }} onClick={loadDashboardData}>
            <RefreshCw size={14} className={loading ? 'loading' : ''} />
            {lastRefresh && <span>MAJ {lastRefresh.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</span>}
          </div>
        </div>
      </div>

      {/* KPIs */}
      <div className="kpi-grid">
        <div className="kpi-card" onClick={() => onNavigate && onNavigate('dossiers')}>
          <div className="kpi-icon blue"><FolderOpen size={28} /></div>
          <div className="kpi-content">
            <div className="kpi-label">Dossiers en cours</div>
            <div className="kpi-value">{data.kpis.dossiers_en_cours}</div>
            <div className="kpi-subtext positive">+{data.kpis.dossiers_nouveaux_mois} ce mois</div>
          </div>
        </div>
        <div className="kpi-card" onClick={() => onNavigate && onNavigate('tresorerie')}>
          <div className="kpi-icon gold"><PiggyBank size={28} /></div>
          <div className="kpi-content">
            <div className="kpi-label">Trésorerie Solde</div>
            <div className="kpi-value">{formatMontant(data.kpis.solde_tresorerie)}</div>
            <div className="kpi-subtext positive">+{formatMontant(data.tresorerie.encaissements_jour.montant)} aujourd'hui</div>
          </div>
        </div>
        <div className="kpi-card" onClick={() => onNavigate && onNavigate('agenda')}>
          <div className="kpi-icon green"><Calendar size={28} /></div>
          <div className="kpi-content">
            <div className="kpi-label">Aujourd'hui RDV/Tâches</div>
            <div className="kpi-value">{data.kpis.rdv_aujourdhui} / {data.kpis.taches_aujourdhui}</div>
            <div className="kpi-subtext">{data.kpis.audiences_aujourdhui} audiences</div>
          </div>
        </div>
        <div className="kpi-card" style={{ borderColor: data.kpis.alertes_urgentes > 0 ? 'var(--danger)' : undefined }}>
          <div className="kpi-icon red"><AlertTriangle size={28} /></div>
          <div className="kpi-content">
            <div className="kpi-label">Alertes urgentes</div>
            <div className="kpi-value" style={{ color: data.kpis.alertes_urgentes > 0 ? 'var(--danger)' : undefined }}>{data.kpis.alertes_urgentes}</div>
            <div className="kpi-subtext" style={{ cursor: 'pointer', color: 'var(--primary)' }}>Voir détails →</div>
          </div>
        </div>
      </div>

      {/* WIDGETS */}
      <div className="dashboard-grid">
        {/* DOSSIERS */}
        <div className="widget">
          <div className="widget-header">
            <div className="widget-title"><div className="widget-title-icon" style={{ background: 'rgba(43, 108, 176, 0.1)' }}><FolderOpen size={18} style={{ color: 'var(--info)' }} /></div>Dossiers</div>
            <span className="widget-link" onClick={() => onNavigate && onNavigate('dossiers')}>Voir tout <ChevronRight size={14} /></span>
          </div>
          <div className="widget-body">
            <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px' }}>RÉPARTITION</div>
            <div className="stat-row"><span className="stat-label">En cours</span><span className="stat-value">{data.dossiers.en_cours} ({Math.round(data.dossiers.en_cours / (data.dossiers.en_cours + data.dossiers.en_attente + data.dossiers.clotures_mois) * 100)}%)</span></div>
            <div className="progress-mini"><div className="progress-mini-fill green" style={{ width: `${Math.round(data.dossiers.en_cours / (data.dossiers.en_cours + data.dossiers.en_attente + data.dossiers.clotures_mois) * 100)}%` }} /></div>
            <div className="stat-row" style={{ marginTop: '8px' }}><span className="stat-label">En attente</span><span className="stat-value">{data.dossiers.en_attente}</span></div>
            <div className="stat-row"><span className="stat-label">Clôturés ce mois</span><span className="stat-value">{data.dossiers.clotures_mois}</span></div>
            <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px', marginTop: '16px' }}>DERNIERS DOSSIERS</div>
            {data.dossiers.derniers.slice(0, 3).map((d, i) => (
              <div key={i} style={{ fontSize: '12px', padding: '6px 0', borderBottom: '1px solid var(--neutral-100)' }}>
                <span style={{ fontWeight: '600', color: 'var(--primary)' }}>{d.reference}</span>
                <span style={{ color: 'var(--neutral-500)', marginLeft: '8px', textTransform: 'capitalize' }}>({d.type_dossier})</span>
              </div>
            ))}
            {data.dossiers.sans_activite_30j > 0 && (
              <div style={{ marginTop: '12px', padding: '8px 12px', background: 'rgba(237, 137, 54, 0.1)', borderRadius: '6px', fontSize: '12px', color: 'var(--warning)' }}>
                <AlertTriangle size={14} style={{ marginRight: '6px' }} />{data.dossiers.sans_activite_30j} dossiers sans activité depuis 30 jours
              </div>
            )}
          </div>
        </div>

        {/* AGENDA */}
        <div className="widget">
          <div className="widget-header">
            <div className="widget-title"><div className="widget-title-icon" style={{ background: 'rgba(47, 133, 90, 0.1)' }}><Calendar size={18} style={{ color: 'var(--success)' }} /></div>Aujourd'hui</div>
            <span className="widget-link" onClick={() => onNavigate && onNavigate('agenda')}>Voir tout <ChevronRight size={14} /></span>
          </div>
          <div className="widget-body">
            <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px' }}>RENDEZ-VOUS</div>
            <div className="rdv-list">
              {data.agenda.rendez_vous.slice(0, 4).map((r, i) => (
                <div key={i} className={`rdv-item ${getRdvClass(r.type)}`}>
                  <span className="rdv-time">{r.heure}</span>
                  <div className="rdv-details"><div className="rdv-title">{r.titre}</div>{r.dossier_ref && <div className="rdv-dossier">{r.dossier_ref}</div>}</div>
                </div>
              ))}
            </div>
            <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px', marginTop: '16px' }}>TÂCHES À FAIRE</div>
            <div className="task-list">
              {data.agenda.taches.slice(0, 4).map((t, i) => (
                <div key={i} className="task-item">
                  <div className={`task-checkbox ${t.statut === 'termine' ? 'done' : ''}`}>{t.statut === 'termine' && <Check size={12} />}</div>
                  <span className={`task-title ${t.statut === 'termine' ? 'done' : ''}`}>{t.titre}</span>
                  {t.priorite === 'urgent' && <span className="task-urgent">Urgent</span>}
                </div>
              ))}
            </div>
            {data.agenda.taches_retard > 0 && (
              <div style={{ marginTop: '12px', padding: '8px 12px', background: 'rgba(197, 48, 48, 0.1)', borderRadius: '6px', fontSize: '12px', color: 'var(--danger)' }}>
                <AlertTriangle size={14} style={{ marginRight: '6px' }} />{data.agenda.taches_retard} tâches en retard
              </div>
            )}
          </div>
        </div>

        {/* TRÉSORERIE */}
        <div className="widget">
          <div className="widget-header">
            <div className="widget-title"><div className="widget-title-icon" style={{ background: 'rgba(198, 169, 98, 0.15)' }}><PiggyBank size={18} style={{ color: 'var(--accent-dark)' }} /></div>Trésorerie</div>
            <span className="widget-link" onClick={() => onNavigate && onNavigate('tresorerie')}>Voir tout <ChevronRight size={14} /></span>
          </div>
          <div className="widget-body">
            <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px' }}>SOLDES</div>
            <table className="data-table"><tbody>
              {data.tresorerie.caisses.map((c, i) => (<tr key={i}><td className="label">{c.nom}</td><td className="value">{formatMontant(c.solde)}</td></tr>))}
              <tr className="total"><td className="label" style={{ fontWeight: '700' }}>TOTAL</td><td className="value" style={{ color: 'var(--accent-dark)' }}>{formatMontant(data.tresorerie.total)}</td></tr>
            </tbody></table>
            <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px', marginTop: '16px' }}>MOUVEMENTS DU JOUR</div>
            <div className="stat-row"><span className="stat-label">↑ Encaissements ({data.tresorerie.encaissements_jour.count})</span><span className="stat-value positive">+{formatMontant(data.tresorerie.encaissements_jour.montant)}</span></div>
            <div className="stat-row"><span className="stat-label">↓ Décaissements ({data.tresorerie.decaissements_jour.count})</span><span className="stat-value negative">-{formatMontant(data.tresorerie.decaissements_jour.montant)}</span></div>
            <div className="stat-row" style={{ background: 'var(--neutral-50)', margin: '8px -12px -8px', padding: '8px 12px', borderRadius: '6px' }}>
              <span className="stat-label" style={{ fontWeight: '600' }}>═ Solde net</span>
              <span className="stat-value" style={{ color: data.tresorerie.encaissements_jour.montant >= data.tresorerie.decaissements_jour.montant ? 'var(--success)' : 'var(--danger)' }}>
                {data.tresorerie.encaissements_jour.montant >= data.tresorerie.decaissements_jour.montant ? '+' : ''}{formatMontant(data.tresorerie.encaissements_jour.montant - data.tresorerie.decaissements_jour.montant)}
              </span>
            </div>
            {data.tresorerie.decaissements_attente > 0 && (
              <div style={{ marginTop: '16px', padding: '8px 12px', background: 'rgba(237, 137, 54, 0.1)', borderRadius: '6px', fontSize: '12px', color: 'var(--warning)' }}>
                <AlertTriangle size={14} style={{ marginRight: '6px' }} />{data.tresorerie.decaissements_attente} décaissements en attente d'approbation
              </div>
            )}
          </div>
        </div>

        {/* FACTURATION */}
        <div className="widget">
          <div className="widget-header">
            <div className="widget-title"><div className="widget-title-icon" style={{ background: 'rgba(128, 90, 213, 0.1)' }}><Receipt size={18} style={{ color: '#805ad5' }} /></div>Facturation</div>
            <span className="widget-link" onClick={() => onNavigate && onNavigate('facturation')}>Voir tout <ChevronRight size={14} /></span>
          </div>
          <div className="widget-body">
            <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px' }}>CE MOIS</div>
            <table className="data-table"><tbody>
              <tr><td className="label">Factures émises</td><td className="value">{data.facturation.emises.count} ({formatMontant(data.facturation.emises.total)})</td></tr>
              <tr><td className="label">Factures payées</td><td className="value" style={{ color: 'var(--success)' }}>{data.facturation.payees.count} ({formatMontant(data.facturation.payees.total)})</td></tr>
              <tr><td className="label">En attente</td><td className="value" style={{ color: 'var(--warning)' }}>{data.facturation.attente.count} ({formatMontant(data.facturation.attente.total)})</td></tr>
            </tbody></table>
            {data.facturation.impayees_30j.length > 0 && (
              <><div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px', marginTop: '16px' }}>IMPAYÉES {">"} 30 JOURS</div>
              {data.facturation.impayees_30j.slice(0, 2).map((f, i) => (<div key={i} style={{ fontSize: '12px', padding: '4px 0', color: 'var(--danger)' }}>• {f.numero} - {formatMontant(f.montant_ttc)} ({f.jours}j)</div>))}</>
            )}
            <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '12px', color: 'var(--neutral-500)' }}>Taux recouvrement :</span>
              <span style={{ fontSize: '16px', fontWeight: '700', color: data.facturation.taux_recouvrement >= 80 ? 'var(--success)' : 'var(--warning)' }}>{data.facturation.taux_recouvrement}%</span>
            </div>
            <div className="progress-mini"><div className="progress-mini-fill green" style={{ width: `${data.facturation.taux_recouvrement}%` }} /></div>
          </div>
        </div>

        {/* COMPTABILITÉ */}
        <div className="widget">
          <div className="widget-header">
            <div className="widget-title"><div className="widget-title-icon" style={{ background: 'rgba(43, 108, 176, 0.1)' }}><BarChart3 size={18} style={{ color: 'var(--info)' }} /></div>Comptabilité</div>
            <span className="widget-link" onClick={() => onNavigate && onNavigate('comptabilite')}>Voir tout <ChevronRight size={14} /></span>
          </div>
          <div className="widget-body">
            <div className="stat-row"><span className="stat-label">Chiffre d'affaires</span><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><span className="stat-value">{formatMontant(data.comptabilite.chiffre_affaires)}</span><span className="trend-badge up"><TrendingUp size={12} /> +12%</span></div></div>
            <div className="stat-row"><span className="stat-label">Charges</span><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><span className="stat-value">{formatMontant(data.comptabilite.charges)}</span><span className="trend-badge down"><TrendingDown size={12} /> -5%</span></div></div>
            <div className="stat-row" style={{ background: 'var(--neutral-50)', margin: '8px -12px 0', padding: '12px', borderRadius: '6px' }}>
              <span className="stat-label" style={{ fontWeight: '600' }}>Résultat net</span>
              <span className="stat-value positive" style={{ fontSize: '18px' }}>{formatMontant(data.comptabilite.resultat_net)}</span>
            </div>
            <div style={{ marginTop: '16px' }}>
              <div style={{ fontSize: '11px', color: 'var(--neutral-500)', marginBottom: '4px' }}>Évolution CA (6 mois)</div>
              <div className="mini-chart">{[65, 72, 80, 68, 85, 100].map((h, i) => (<div key={i} className="mini-chart-bar" style={{ height: `${h}%` }} />))}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: 'var(--neutral-400)', marginTop: '4px' }}><span>Juin</span><span>Juil</span><span>Août</span><span>Sept</span><span>Oct</span><span>Nov</span></div>
            </div>
            {data.comptabilite.tva_a_declarer > 0 && (
              <div style={{ marginTop: '12px', padding: '8px 12px', background: 'rgba(237, 137, 54, 0.1)', borderRadius: '6px', fontSize: '12px', color: 'var(--warning)' }}>
                <AlertTriangle size={14} style={{ marginRight: '6px' }} />TVA à déclarer : {formatMontant(data.comptabilite.tva_a_declarer)}
              </div>
            )}
          </div>
        </div>

        {/* RECOUVREMENT */}
        <div className="widget">
          <div className="widget-header">
            <div className="widget-title"><div className="widget-title-icon" style={{ background: 'rgba(197, 48, 48, 0.1)' }}><Scale size={18} style={{ color: 'var(--danger)' }} /></div>Recouvrement</div>
            <span className="widget-link" onClick={() => onNavigate && onNavigate('calcul')}>Voir tout <ChevronRight size={14} /></span>
          </div>
          <div className="widget-body">
            <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px' }}>PORTEFEUILLE</div>
            <table className="data-table"><tbody>
              <tr><td className="label">Amiables</td><td className="value">{data.recouvrement.amiables.count} ({formatMontant(data.recouvrement.amiables.total)})</td></tr>
              <tr><td className="label">Forcés</td><td className="value">{data.recouvrement.forces.count} ({formatMontant(data.recouvrement.forces.total)})</td></tr>
              <tr className="total"><td className="label" style={{ fontWeight: '700' }}>TOTAL</td><td className="value">{formatMontant(data.recouvrement.total_creances)}</td></tr>
            </tbody></table>
            <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px', marginTop: '16px' }}>CE MOIS</div>
            <div className="stat-row"><span className="stat-label">↑ Encaissé</span><span className="stat-value positive">{formatMontant(data.recouvrement.encaissements_mois)}</span></div>
            <div className="stat-row"><span className="stat-label">↓ Reversé</span><span className="stat-value">{formatMontant(data.recouvrement.reversements_mois)}</span></div>
            <div className="stat-row"><span className="stat-label">💼 Émoluments</span><span className="stat-value" style={{ color: 'var(--accent-dark)' }}>{formatMontant(data.recouvrement.emoluments_mois)}</span></div>
            <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px', color: 'var(--neutral-500)' }}>Taux global :</span>
              <span style={{ fontSize: '16px', fontWeight: '700', color: 'var(--info)' }}>{data.recouvrement.taux_recouvrement}%</span>
            </div>
          </div>
        </div>

        {/* GÉRANCE */}
        <div className="widget">
          <div className="widget-header">
            <div className="widget-title"><div className="widget-title-icon" style={{ background: 'rgba(47, 133, 90, 0.1)' }}><Building2 size={18} style={{ color: 'var(--success)' }} /></div>Gérance Immobilière</div>
            <span className="widget-link" onClick={() => onNavigate && onNavigate('gerance')}>Voir tout <ChevronRight size={14} /></span>
          </div>
          <div className="widget-body">
            <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px' }}>PARC IMMOBILIER</div>
            <table className="data-table"><tbody>
              <tr><td className="label">Biens gérés</td><td className="value">{data.gerance.biens_gestion}</td></tr>
              <tr><td className="label">Loués</td><td className="value" style={{ color: 'var(--success)' }}>{data.gerance.biens_loues} ({data.gerance.taux_occupation}%)</td></tr>
              <tr><td className="label">Vacants</td><td className="value" style={{ color: 'var(--warning)' }}>{data.gerance.biens_vacants}</td></tr>
            </tbody></table>
            <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px', marginTop: '16px' }}>LOYERS</div>
            <div className="stat-row"><span className="stat-label">Attendus</span><span className="stat-value">{formatMontant(data.gerance.loyers_attendus)}</span></div>
            <div className="stat-row"><span className="stat-label">Encaissés</span><span className="stat-value positive">{formatMontant(data.gerance.loyers_encaisses)}</span></div>
            <div className="stat-row"><span className="stat-label">Impayés</span><span className="stat-value negative">{formatMontant(data.gerance.loyers_impayes)}</span></div>
            <div className="progress-mini"><div className="progress-mini-fill green" style={{ width: `${Math.round(data.gerance.loyers_encaisses / data.gerance.loyers_attendus * 100)}%` }} /></div>
          </div>
        </div>

        {/* RH */}
        <div className="widget">
          <div className="widget-header">
            <div className="widget-title"><div className="widget-title-icon" style={{ background: 'rgba(128, 90, 213, 0.1)' }}><Users size={18} style={{ color: '#805ad5' }} /></div>Équipe</div>
            <span className="widget-link" onClick={() => onNavigate && onNavigate('rh')}>Voir tout <ChevronRight size={14} /></span>
          </div>
          <div className="widget-body">
            <table className="data-table"><tbody>
              <tr><td className="label">Total employés</td><td className="value">{data.rh.effectif_total}</td></tr>
              <tr><td className="label">Présents</td><td className="value" style={{ color: 'var(--success)' }}>{data.rh.presents_aujourdhui}</td></tr>
              <tr><td className="label">En congé</td><td className="value" style={{ color: 'var(--info)' }}>{data.rh.en_conge}</td></tr>
            </tbody></table>
            {data.rh.conges_en_cours.length > 0 && (
              <><div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px', marginTop: '16px' }}>CONGÉS</div>
              {data.rh.conges_en_cours.map((c, i) => (<div key={i} style={{ fontSize: '12px', padding: '4px 0' }}>• {c.employe} - jusqu'au {c.date_fin}</div>))}</>
            )}
            {data.rh.alertes.length > 0 && (
              <><div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px', marginTop: '16px' }}>ALERTES</div>
              {data.rh.alertes.slice(0, 2).map((a, i) => (<div key={i} style={{ padding: '6px 10px', background: 'rgba(237, 137, 54, 0.1)', borderRadius: '6px', fontSize: '11px', color: 'var(--warning)', marginBottom: '4px' }}>⚠️ {a.message}</div>))}</>
            )}
          </div>
        </div>

        {/* MÉMOIRES */}
        <div className="widget">
          <div className="widget-header">
            <div className="widget-title"><div className="widget-title-icon" style={{ background: 'rgba(198, 169, 98, 0.15)' }}><FileSignature size={18} style={{ color: 'var(--accent-dark)' }} /></div>Mémoires de Cédules</div>
            <span className="widget-link" onClick={() => onNavigate && onNavigate('memoires')}>Voir tout <ChevronRight size={14} /></span>
          </div>
          <div className="widget-body">
            <table className="data-table"><tbody>
              <tr><td className="label">En attente paiement</td><td className="value">{data.memoires.attente_paiement.count} ({formatMontant(data.memoires.attente_paiement.total)})</td></tr>
              <tr><td className="label">Payés ce mois</td><td className="value" style={{ color: 'var(--success)' }}>{data.memoires.payes_mois.count} ({formatMontant(data.memoires.payes_mois.total)})</td></tr>
              <tr><td className="label">Cédules en cours</td><td className="value">{data.memoires.cedules_en_cours}</td></tr>
            </tbody></table>
            {data.memoires.attente_longue.length > 0 && (
              <><div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--neutral-500)', marginBottom: '8px', marginTop: '16px' }}>EN ATTENTE LONGUE</div>
              {data.memoires.attente_longue.slice(0, 2).map((m, i) => (<div key={i} style={{ padding: '6px 10px', background: 'rgba(237, 137, 54, 0.1)', borderRadius: '6px', fontSize: '11px', color: 'var(--warning)', marginBottom: '4px' }}>⚠️ N°{m.numero} - {formatMontant(m.montant_total)} ({m.jours}j)</div>))}</>
            )}
          </div>
        </div>

        {/* ALERTES */}
        <div className="widget full-width">
          <div className="widget-header">
            <div className="widget-title"><div className="widget-title-icon" style={{ background: 'rgba(197, 48, 48, 0.1)' }}><Bell size={18} style={{ color: 'var(--danger)' }} /></div>Alertes ({(data.alertes.urgentes?.length||0) + (data.alertes.importantes?.length||0) + (data.alertes.informations?.length||0)})</div>
          </div>
          <div className="widget-body">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
              <div className="alert-section">
                <div className="alert-section-title urgent">🔴 URGENTES ({data.alertes.urgentes?.length || 0})</div>
                {data.alertes.urgentes?.map((a, i) => (<div key={i} className="alert-item urgent">• {a.message}</div>))}
              </div>
              <div className="alert-section">
                <div className="alert-section-title important">🟠 IMPORTANTES ({data.alertes.importantes?.length || 0})</div>
                {data.alertes.importantes?.map((a, i) => (<div key={i} className="alert-item important">• {a.message}</div>))}
              </div>
              <div className="alert-section">
                <div className="alert-section-title info">🟡 INFORMATIONS ({data.alertes.informations?.length || 0})</div>
                {data.alertes.informations?.map((a, i) => (<div key={i} className="alert-item info">• {a.message}</div>))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ACTIONS RAPIDES */}
      <div className="quick-actions no-print">
        <button className="quick-action-btn primary" onClick={() => onOpenModal && onOpenModal('nouveau-dossier')}><Plus size={16} /> Nouveau Dossier</button>
        <button className="quick-action-btn" onClick={() => onNavigate && onNavigate('facturation')}><Plus size={16} /> Facture</button>
        <button className="quick-action-btn" onClick={() => onNavigate && onNavigate('encaissements')}><Plus size={16} /> Encaissement</button>
        <button className="quick-action-btn" onClick={() => onNavigate && onNavigate('agenda')}><Plus size={16} /> RDV</button>
        <button className="quick-action-btn"><Search size={16} /> Recherche</button>
      </div>
    </div>
  );
};

const DashboardModule = ({ onNavigate, onOpenModal }) => <AdvancedDashboard onNavigate={onNavigate} onOpenModal={onOpenModal} />;

// ============================================
// CHATBOT
// ============================================
const Chatbot = () => {
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState([{ type: 'bot', txt: 'Bonjour Maître, je suis votre assistant. Comment puis-je vous aider ?' }]);
  const [input, setInput] = useState('');
  
  const send = () => { 
    if(!input.trim()) return; 
    setMsgs([...msgs, { type: 'user', txt: input }]); 
    const userMsg = input;
    setInput(''); 
    setTimeout(() => { 
      let rep = "Je peux vous aider à rédiger des actes, calculer des intérêts ou rechercher des informations juridiques."; 
      if(userMsg.toLowerCase().includes('supprim') && CURRENT_USER.role !== 'admin') {
        rep = "Désolé, seul l'administrateur peut supprimer des éléments.";
      } else if(userMsg.toLowerCase().includes('intérêt') || userMsg.toLowerCase().includes('calcul')) {
        rep = "Pour calculer des intérêts, rendez-vous dans le module 'Calcul Recouvrement'. Je peux vous y guider si vous le souhaitez.";
      } else if(userMsg.toLowerCase().includes('dossier')) {
        rep = "Pour créer ou consulter un dossier, utilisez le module 'Dossiers'. Vous pouvez cliquer sur 'Nouveau dossier' pour en créer un.";
      }
      setMsgs(prev => [...prev, { type: 'bot', txt: rep }]); 
    }, 500); 
  };
  
  return (
    <div className="chatbot-container no-print">
      {open && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <Bot size={20} />
            <span style={{ fontWeight: '600' }}>Assistant Juridique</span>
            <button style={{marginLeft:'auto', background:'none', border:'none', color:'white', cursor: 'pointer'}} onClick={() => setOpen(false)}><X size={18}/></button>
          </div>
          <div className="chatbot-messages">
            {msgs.map((m, i) => <div key={i} className={`chat-message ${m.type}`}>{m.txt}</div>)}
          </div>
          <div className="chatbot-input-area">
            <input className="form-input" style={{ flex: 1 }} placeholder="Votre question..." value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key==='Enter' && send()} />
            <button className="btn btn-primary" onClick={send}><Send size={16}/></button>
          </div>
        </div>
      )}
      <button 
        onClick={() => setOpen(!open)}
        style={{
          width: '56px', 
          height: '56px', 
          borderRadius: '50%', 
          background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%)', 
          color: 'white', 
          border: 'none',
          cursor: 'pointer',
          boxShadow: 'var(--shadow-lg)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <MessageSquare size={24} />
      </button>
    </div>
  );
};

// ============================================
// APP PRINCIPALE
// ============================================
export default function App() {
  const [active, setActive] = useState('dashboard');
  const [modal, setModal] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const renderModule = () => {
    switch (active) {
      case 'dashboard': return <DashboardModule onNavigate={setActive} onOpenModal={setModal} />;
      case 'dossiers': return <DossiersModule onOpenModal={setModal} />;
      case 'facturation': return <FacturationModule />;
      case 'calcul': return <CalculRecouvrementModule />;
      case 'drive': return <DriveModule />;
      case 'securite': return <SecuriteModule />;
      default: return (
        <div className="card">
          <div className="card-body" style={{ textAlign: 'center', padding: '60px' }}>
            <Settings size={48} style={{ color: 'var(--neutral-300)', marginBottom: '16px' }} />
            <h3 style={{ color: 'var(--neutral-500)', marginBottom: '8px' }}>Module en construction</h3>
            <p style={{ color: 'var(--neutral-400)', fontSize: '14px' }}>Ce module sera bientôt disponible.</p>
          </div>
        </div>
      );
    }
  };

  return (
    <>
      <style>{styles}</style>
      <div className="app-container">
        <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
          <div className="sidebar-header">
            <div className="logo">
              <div className="logo-icon">MAB</div>
              <div>
                <div className="logo-text">Étude BIAOU</div>
                <div className="logo-subtitle">Huissier de Justice</div>
              </div>
            </div>
          </div>
          <nav className="sidebar-nav">
            <div className="nav-section">
              <div className="nav-section-title">Principal</div>
              {MODULES_LIST.filter(m => m.category === 'main').map(m => (
                <div key={m.id} className={`nav-item ${active === m.id ? 'active' : ''}`} onClick={() => { setActive(m.id); setSidebarOpen(false); }}>
                  <m.icon size={18} /> {m.label} {m.badge && <span className="nav-badge">{m.badge}</span>}
                </div>
              ))}
            </div>
            <div className="nav-section">
              <div className="nav-section-title">Finance</div>
              {MODULES_LIST.filter(m => m.category === 'finance').map(m => (
                <div key={m.id} className={`nav-item ${active === m.id ? 'active' : ''}`} onClick={() => { setActive(m.id); setSidebarOpen(false); }}>
                  <m.icon size={18} /> {m.label}
                </div>
              ))}
            </div>
            <div className="nav-section">
              <div className="nav-section-title">Gestion</div>
              {MODULES_LIST.filter(m => m.category === 'gestion').map(m => (
                <div key={m.id} className={`nav-item ${active === m.id ? 'active' : ''}`} onClick={() => { setActive(m.id); setSidebarOpen(false); }}>
                  <m.icon size={18} /> {m.label}
                </div>
              ))}
            </div>
            <div className="nav-section">
              <div className="nav-section-title">Administration</div>
              {MODULES_LIST.filter(m => m.category === 'admin').map(m => (
                <div key={m.id} className={`nav-item ${active === m.id ? 'active' : ''}`} onClick={() => { setActive(m.id); setSidebarOpen(false); }}>
                  <m.icon size={18} /> {m.label}
                </div>
              ))}
            </div>
          </nav>
          <div className="sidebar-footer">
            <div className="user-card">
              <div className="user-avatar">MA</div>
              <div className="user-info">
                <div style={{fontSize:'12px', fontWeight:'bold'}}>{CURRENT_USER.nom}</div>
                <div style={{fontSize:'10px', opacity:0.8}}>Administrateur</div>
              </div>
            </div>
          </div>
        </aside>
        <main className="main-content">
          <header className="topbar">
            <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}><Menu size={24}/></button>
            <h1 className="page-title">{MODULES_LIST.find(m => m.id === active)?.label || 'Module'}</h1>
            <div className="search-bar">
              <Search />
              <input type="text" placeholder="Rechercher..." />
            </div>
            <div className="topbar-actions">
              <button className="icon-btn"><Bell size={18} /></button>
              <button className="icon-btn"><User size={18} /></button>
            </div>
          </header>
          <div className="page-content">{renderModule()}</div>
        </main>
        <Chatbot />
        {modal === 'nouveau-dossier' && <NouveauDossierModal onClose={() => setModal(null)} />}
      </div>
    </>
  );
}
