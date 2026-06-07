'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Globe, Phone, Mail, MapPin, ShieldAlert, Activity, AlertTriangle, CheckCircle, Database, Server, Bitcoin, User, Network } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

type EntityType = 'IP' | 'PHONE' | 'EMAIL' | 'DOMAIN' | 'CRYPTO' | 'USERNAME';

export default function OSINTDashboard() {
  const { token } = useAuth();
  const [entityType, setEntityType] = useState<EntityType>('IP');
  const [entityValue, setEntityValue] = useState('');
  const [searchQuery, setSearchQuery] = useState<{ type: EntityType, value: string } | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['osint', searchQuery?.type, searchQuery?.value],
    queryFn: async () => {
      if (!searchQuery) return null;
      const res = await fetch(`http://localhost:8001/api/v1/enrichment/osint/${searchQuery.type}?entity_value=${encodeURIComponent(searchQuery.value)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('OSINT lookup failed');
      return res.json();
    },
    enabled: !!searchQuery && !!token,
    retry: false
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!entityValue.trim()) return;
    setSearchQuery({ type: entityType, value: entityValue.trim() });
  };

  const renderRiskScore = (score: number) => {
    if (score >= 0.7) return <span className="text-error-400 font-bold flex items-center gap-1"><AlertTriangle className="w-4 h-4"/> CRITICAL ({score})</span>;
    if (score >= 0.4) return <span className="text-warning-400 font-bold flex items-center gap-1"><Activity className="w-4 h-4"/> SUSPICIOUS ({score})</span>;
    return <span className="text-success-400 font-bold flex items-center gap-1"><CheckCircle className="w-4 h-4"/> BENIGN ({score})</span>;
  };

  const renderIPIntelligence = (data: any) => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
      <div className="bg-background-surface border border-border-default rounded-xl p-6">
        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
          <MapPin className="text-primary-400" /> Geolocation
        </h3>
        <dl className="space-y-4">
          <div><dt className="text-sm text-text-muted font-mono">Country</dt><dd className="text-lg text-text-primary">{data.geolocation.country}</dd></div>
          <div><dt className="text-sm text-text-muted font-mono">Coordinates</dt><dd className="font-mono text-text-secondary">{data.geolocation.latitude}, {data.geolocation.longitude}</dd></div>
        </dl>
      </div>
      <div className="bg-background-surface border border-border-default rounded-xl p-6">
        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
          <Server className="text-warning-400" /> Infrastructure
        </h3>
        <dl className="space-y-4">
          <div><dt className="text-sm text-text-muted font-mono">ASN</dt><dd className="font-mono text-text-primary">{data.asn.number} - {data.asn.organization}</dd></div>
          <div className="grid grid-cols-2 gap-4">
            <div><dt className="text-sm text-text-muted font-mono">VPN / Proxy</dt><dd className="text-text-primary">{data.threat_intel.is_vpn || data.threat_intel.is_proxy ? 'DETECTED' : 'CLEAN'}</dd></div>
            <div><dt className="text-sm text-text-muted font-mono">Abuse Reports</dt><dd className="text-text-primary">{data.threat_intel.recent_abuse_reports}</dd></div>
          </div>
        </dl>
      </div>
    </div>
  );

  const renderPhoneIntelligence = (data: any) => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
      <div className="bg-background-surface border border-border-default rounded-xl p-6">
        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
          <Phone className="text-primary-400" /> Caller Identity
        </h3>
        <dl className="space-y-4">
          <div><dt className="text-sm text-text-muted font-mono">Registered Name</dt><dd className="text-lg text-text-primary">{data.caller_id.name}</dd></div>
          <div><dt className="text-sm text-text-muted font-mono">Carrier / Line</dt><dd className="text-text-secondary">{data.caller_id.carrier} ({data.caller_id.line_type})</dd></div>
        </dl>
      </div>
      <div className="bg-background-surface border border-border-default rounded-xl p-6">
        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
          <ShieldAlert className="text-error-400" /> Spam Reputation
        </h3>
        <dl className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
             <div><dt className="text-sm text-text-muted font-mono">Spam Score</dt><dd className="text-xl font-bold text-text-primary">{data.spam_reputation.spam_score}/100</dd></div>
             <div><dt className="text-sm text-text-muted font-mono">User Reports</dt><dd className="text-text-primary">{data.spam_reputation.user_reports}</dd></div>
          </div>
          <div>
            <dt className="text-sm text-text-muted font-mono">Tags</dt>
            <dd className="flex gap-2 mt-1">
              {data.spam_reputation.tags.length > 0 ? data.spam_reputation.tags.map((t: string) => (
                <span key={t} className="px-2 py-1 bg-error-500/10 text-error-400 text-xs rounded border border-error-500/20">{t}</span>
              )) : <span className="text-text-secondary text-sm">No malicious tags</span>}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  );

  const renderEmailIntelligence = (data: any) => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
      <div className="bg-background-surface border border-border-default rounded-xl p-6">
        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
          <Database className="text-error-400" /> Breach Intelligence
        </h3>
        <dl className="space-y-4">
          <div><dt className="text-sm text-text-muted font-mono">Known Breaches (Pwned)</dt><dd className="text-xl font-bold text-text-primary">{data.breach_monitoring.pwned_count}</dd></div>
          <div><dt className="text-sm text-text-muted font-mono">Latest Breach Event</dt><dd className="text-text-secondary">{data.breach_monitoring.latest_breach || 'None on record'}</dd></div>
        </dl>
      </div>
      <div className="bg-background-surface border border-border-default rounded-xl p-6">
        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
          <Mail className="text-primary-400" /> Domain & Inbox
        </h3>
        <dl className="space-y-4">
          <div><dt className="text-sm text-text-muted font-mono">Domain</dt><dd className="text-text-primary">{data.domain_reputation.domain} {data.domain_reputation.is_disposable && <span className="text-error-400 text-xs border border-error-400 px-1 ml-2">DISPOSABLE</span>}</dd></div>
          <div><dt className="text-sm text-text-muted font-mono">SMTP Reachable</dt><dd className="text-text-secondary">{data.deliverability.smtp_reachable ? 'YES' : 'NO'}</dd></div>
        </dl>
      </div>
    </div>
  );

  const renderDomainIntelligence = (data: any) => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
      <div className="bg-background-surface border border-border-default rounded-xl p-6">
        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
          <Globe className="text-primary-400" /> WHOIS Registration
        </h3>
        <dl className="space-y-4">
          <div><dt className="text-sm text-text-muted font-mono">Registrar</dt><dd className="text-text-primary">{data.whois.registrar}</dd></div>
          <div className="grid grid-cols-2 gap-4">
             <div><dt className="text-sm text-text-muted font-mono">Creation Date</dt><dd className="text-text-primary">{data.whois.creation_date}</dd></div>
             <div><dt className="text-sm text-text-muted font-mono">Days Old</dt><dd className="text-text-primary font-mono">{data.whois.days_old}</dd></div>
          </div>
        </dl>
      </div>
      <div className="bg-background-surface border border-border-default rounded-xl p-6">
        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
          <Activity className="text-warning-400" /> Threat Intel
        </h3>
        <dl className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
             <div><dt className="text-sm text-text-muted font-mono">Phishing List</dt><dd className={data.threat_intel.phishing_detected ? 'text-error-400' : 'text-text-secondary'}>{data.threat_intel.phishing_detected ? 'FLAGGED' : 'CLEAN'}</dd></div>
             <div><dt className="text-sm text-text-muted font-mono">Malware Hosted</dt><dd className={data.threat_intel.malware_hosted ? 'text-error-400' : 'text-text-secondary'}>{data.threat_intel.malware_hosted ? 'FLAGGED' : 'CLEAN'}</dd></div>
          </div>
          <div><dt className="text-sm text-text-muted font-mono">A Records (Resolved IP)</dt><dd className="text-text-secondary font-mono text-sm">{data.dns.a_records.join(', ')}</dd></div>
        </dl>
      </div>
    </div>
  );

  const renderCryptoIntelligence = (data: any) => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
      <div className="bg-background-surface border border-border-default rounded-xl p-6">
        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
          <Bitcoin className="text-warning-400" /> Blockchain Data
        </h3>
        <dl className="space-y-4">
          <div><dt className="text-sm text-text-muted font-mono">Network</dt><dd className="text-lg text-text-primary font-bold">{data.blockchain_data.network}</dd></div>
          <div className="grid grid-cols-2 gap-4">
             <div><dt className="text-sm text-text-muted font-mono">Balance</dt><dd className="text-xl text-primary-400 font-mono">{data.blockchain_data.balance}</dd></div>
             <div><dt className="text-sm text-text-muted font-mono">Tx Count</dt><dd className="text-text-primary font-mono">{data.blockchain_data.total_transactions}</dd></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
             <div><dt className="text-sm text-text-muted font-mono">First Seen</dt><dd className="text-text-secondary">{data.blockchain_data.first_seen}</dd></div>
             <div><dt className="text-sm text-text-muted font-mono">Last Seen</dt><dd className="text-text-secondary">{data.blockchain_data.last_seen}</dd></div>
          </div>
        </dl>
      </div>
      <div className="bg-background-surface border border-border-default rounded-xl p-6 border-l-4 border-l-error-500">
        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
          <Network className="text-error-400" /> Forensic Attribution
        </h3>
        <dl className="space-y-4">
          <div><dt className="text-sm text-text-muted font-mono">Identified Cluster</dt><dd className="text-xl font-bold text-error-400">{data.forensic_attribution.identified_cluster}</dd></div>
          <div><dt className="text-sm text-text-muted font-mono">Exchange Hot Wallet</dt><dd className="text-text-secondary">{data.forensic_attribution.is_exchange_hot_wallet ? 'YES' : 'NO'}</dd></div>
          <div>
             <dt className="text-sm text-text-muted font-mono mb-2">Illicit Exposure</dt>
             <div className="w-full bg-background-base rounded-full h-2.5">
               <div className="bg-error-500 h-2.5 rounded-full" style={{ width: `${data.forensic_attribution.illicit_exposure_pct}%` }}></div>
             </div>
             <dd className="text-text-secondary text-right mt-1 text-xs">{data.forensic_attribution.illicit_exposure_pct}%</dd>
          </div>
        </dl>
      </div>
    </div>
  );

  const renderUsernameIntelligence = (data: any) => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
      <div className="bg-background-surface border border-border-default rounded-xl p-6">
        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
          <User className="text-primary-400" /> Social Footprint
        </h3>
        <div className="space-y-3">
          <div className="text-sm text-text-muted font-mono mb-4">Searched across {data.social_footprint.platforms_checked} platforms</div>
          {data.social_footprint.details.map((plat: any, i: number) => (
             <div key={i} className="flex items-center justify-between p-3 bg-background-base rounded border border-border-default">
               <span className="font-semibold text-text-primary">{plat.name}</span>
               <span className={plat.found ? 'text-success-400 font-bold text-sm bg-success-500/10 px-2 py-1 rounded' : 'text-text-muted text-sm'}>
                 {plat.found ? 'FOUND' : 'NOT FOUND'}
               </span>
             </div>
          ))}
        </div>
      </div>
      <div className="bg-background-surface border border-border-default rounded-xl p-6">
        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2 mb-4">
          <Search className="text-warning-400" /> Extracted Intel
        </h3>
        <dl className="space-y-4">
          <div><dt className="text-sm text-text-muted font-mono">Possible Real Name</dt><dd className="text-lg text-text-primary">{data.extracted_intel.possible_real_name || 'Unknown'}</dd></div>
          <div><dt className="text-sm text-text-muted font-mono">Bio Snippet</dt><dd className="text-text-secondary italic border-l-2 border-border-default pl-3 mt-1">{data.extracted_intel.bio_snippet}</dd></div>
          {data.extracted_intel.associated_locations.length > 0 && (
            <div><dt className="text-sm text-text-muted font-mono">Associated Locations</dt><dd className="text-text-primary mt-1">{data.extracted_intel.associated_locations.join(', ')}</dd></div>
          )}
        </dl>
      </div>
    </div>
  );

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <Globe className="text-primary-400 w-6 h-6" /> External OSINT Intelligence
        </h1>
        <p className="text-text-secondary">Simulated aggregation of external registries (Truecaller, Shodan, WHOIS, HIBP).</p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="flex gap-4">
        <select 
          value={entityType} 
          onChange={(e) => setEntityType(e.target.value as EntityType)}
          className="bg-background-surface border border-border-default text-text-primary rounded-xl px-4 py-3 focus:outline-none focus:border-primary-500 font-mono"
        >
          <option value="IP">IP Address</option>
          <option value="PHONE">Phone Number</option>
          <option value="EMAIL">Email Address</option>
          <option value="DOMAIN">Domain Name</option>
          <option value="CRYPTO">Crypto Wallet</option>
          <option value="USERNAME">Social Username</option>
        </select>
        <input 
          type="text" 
          value={entityValue}
          onChange={(e) => setEntityValue(e.target.value)}
          placeholder={entityType === 'IP' ? 'e.g., 103.45.67.89' : entityType === 'PHONE' ? 'e.g., 9876543210' : entityType === 'CRYPTO' ? 'e.g., bc1q...' : entityType === 'USERNAME' ? 'e.g., scammer99' : `e.g., suspect@${entityType.toLowerCase()}`}
          className="flex-1 bg-background-surface border border-border-default text-text-primary rounded-xl px-4 py-3 focus:outline-none focus:border-primary-500 font-mono"
        />
        <button 
          type="submit"
          className="bg-primary-600 hover:bg-primary-500 text-white px-8 py-3 rounded-xl transition-colors font-bold flex items-center gap-2"
        >
          <Search className="w-5 h-5" /> SCAN
        </button>
      </form>

      {/* Results */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center p-12 text-text-muted">
           <Search className="w-12 h-12 mb-4 animate-bounce text-primary-500" />
           <p className="font-mono animate-pulse">Querying external OSINT databases...</p>
        </div>
      )}

      {error && (
        <div className="p-4 bg-error-500/10 border border-error-500/20 text-error-400 rounded-xl font-mono">
          Could not retrieve intelligence. Ensure the backend is running.
        </div>
      )}

      {data && !isLoading && (
        <div className="animate-in fade-in slide-in-from-bottom-4">
          <div className="flex items-center justify-between border-b border-border-default pb-4">
             <div>
               <h2 className="text-xl font-mono font-bold text-text-primary">{data.entity}</h2>
               <span className="text-sm text-text-muted uppercase tracking-widest">{data.type} INTELLIGENCE REPORT</span>
             </div>
             <div className="text-right">
               <div className="text-sm text-text-muted mb-1">Composite Risk</div>
               {renderRiskScore(data.risk_score)}
             </div>
          </div>
          
          {data.type === 'IP' && renderIPIntelligence(data.data)}
          {data.type === 'PHONE' && renderPhoneIntelligence(data.data)}
          {data.type === 'EMAIL' && renderEmailIntelligence(data.data)}
          {data.type === 'DOMAIN' && renderDomainIntelligence(data.data)}
          {data.type === 'CRYPTO' && renderCryptoIntelligence(data.data)}
          {data.type === 'USERNAME' && renderUsernameIntelligence(data.data)}
        </div>
      )}
    </div>
  );
}
