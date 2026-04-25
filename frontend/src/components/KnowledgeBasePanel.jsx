import React, { useState, useEffect } from 'react';
import { BookOpen, Search, ExternalLink, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

export default function KnowledgeBasePanel({ projectId, contractorCIDB }) {
  const [sources, setSources] = useState([]);
  const [blacklistStatus, setBlacklistStatus] = useState(null);
  const [isChecking, setIsChecking] = useState(false);

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      setSources([
        { id: 'cidb-act-1994', title: 'CIDB Act 1994', type: 'regulation', indexed: false },
        { id: 'bisq-standards', title: 'BISQ Quality Standards', type: 'standard', indexed: false },
        { id: 'construction-guidelines', title: 'Construction Best Practices', type: 'guideline', indexed: false }
      ]);
    } catch (error) {
      console.error('Error fetching KB sources:', error);
    }
  };

  const checkContractorBlacklist = async () => {
    if (!contractorCIDB) {
      setBlacklistStatus({ status: 'error', message: 'No CIDB registration found' });
      return;
    }

    setIsChecking(true);
    setTimeout(() => {
      setBlacklistStatus({
        status: 'pending',
        message: 'Blacklist verification pending CIDB API integration',
        cidb_registration: contractorCIDB
      });
      setIsChecking(false);
    }, 1000);
  };

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-[#ff6b35]" />
            <h3 className="font-semibold text-lg text-[#1c1b18]">Contractor Verification</h3>
          </div>
          <span className="text-xs text-[#9b9794] bg-yellow-100 px-2 py-1 rounded">Integration Pending</span>
        </div>

        {contractorCIDB ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg bg-[#f5f4f0]">
              <div>
                <p className="text-xs text-[#9b9794] uppercase tracking-wider">CIDB Registration</p>
                <p className="text-sm font-semibold text-[#1c1b18] mt-1">{contractorCIDB}</p>
              </div>
              <button
                onClick={checkContractorBlacklist}
                disabled={isChecking}
                className="px-4 py-2 rounded-lg bg-[#ff6b35] text-white text-sm hover:bg-[#e55a2b] disabled:opacity-50 transition-colors"
              >
                {isChecking ? 'Checking...' : 'Verify'}
              </button>
            </div>

            {blacklistStatus && (
              <div className={`p-4 rounded-lg border ${
                blacklistStatus.status === 'clear' ? 'bg-green-50 border-green-200' :
                blacklistStatus.status === 'blacklisted' ? 'bg-red-50 border-red-200' :
                blacklistStatus.status === 'error' ? 'bg-red-50 border-red-200' :
                'bg-yellow-50 border-yellow-200'
              }`}>
                <div className="flex items-start gap-3">
                  {blacklistStatus.status === 'clear' && <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />}
                  {blacklistStatus.status === 'blacklisted' && <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />}
                  {(blacklistStatus.status === 'error' || blacklistStatus.status === 'pending') && <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />}
                  <p className="text-sm font-medium text-[#1c1b18]">{blacklistStatus.message}</p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-[#6b6860]">No CIDB registration found. Upload project documents to extract contractor information.</p>
        )}
      </div>

      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-[#ff6b35]" />
            <h3 className="font-semibold text-lg text-[#1c1b18]">Knowledge Base</h3>
          </div>
          <span className="text-xs text-[#9b9794]">{sources.filter(s => s.indexed).length} / {sources.length} indexed</span>
        </div>

        <div className="space-y-3">
          {sources.map(source => (
            <div key={source.id} className="flex items-center justify-between p-4 rounded-lg border border-[#e4e2dc] hover:bg-[#f5f4f0] transition-colors">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-[#1c1b18]">{source.title}</h4>
                  <span className={`text-[10px] px-2 py-0.5 rounded ${source.indexed ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                    {source.indexed ? 'Indexed' : 'Pending'}
                  </span>
                </div>
                <p className="text-xs text-[#9b9794] mt-1 capitalize">{source.type}</p>
              </div>
              <button className="p-2 rounded-lg hover:bg-[#e4e2dc] transition-colors">
                <ExternalLink className="w-4 h-4 text-[#9b9794]" />
              </button>
            </div>
          ))}
        </div>

        <div className="mt-4 p-4 rounded-lg bg-blue-50 border border-blue-100">
          <p className="text-xs text-blue-700">🚧 Knowledge base integration in progress. Will include CIDB regulations, BISQ standards, and construction guidelines.</p>
        </div>
      </div>
    </div>
  );
}
