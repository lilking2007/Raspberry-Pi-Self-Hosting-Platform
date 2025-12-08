import React, { useEffect, useState } from 'react';
import api from '../api';

export default function Dashboard() {
    const [sites, setSites] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

    // New Site Form
    const [slug, setSlug] = useState('');
    const [displayName, setDisplayName] = useState('');
    const [domain, setDomain] = useState('');
    const [jsonFile, setJsonFile] = useState(null); // Actually we upload zip separately?
    // Blueprint: "User logs into Admin UI and creates a new site entry... User uploads site.zip"
    // So 2 steps or 1?
    // Let's do 1 step wizard or 2 steps.
    // Implementation Plan: Create Site Metadata -> Then Upload.

    const fetchSites = async () => {
        try {
            const res = await api.get('/sites/');
            setSites(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSites();
    }, []);

    const handleCreateSite = async (e) => {
        e.preventDefault();
        try {
            // 1. Create Metadata
            const res = await api.post('/sites/', {
                slug,
                display_name: displayName,
                domain: domain || undefined,
                visibility: 'public' // Default for MVP
            });

            const newSite = res.data;

            // 2. Upload Zip if present (actually we should ask for it)
            // For MVP, simplistic flow.
            alert('Site created! Now upload your content.');
            setSites([...sites, newSite]);
            setShowModal(false);
            setSlug('');
        } catch (err) {
            alert('Failed to create site');
        }
    };

    const handleUpload = async (slug, file) => {
        const formData = new FormData();
        formData.append('file', file);
        try {
            await api.post(`/sites/${slug}/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            alert('Upload started!');
            fetchSites(); // Refresh status
        } catch (err) {
            alert('Upload failed');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <nav className="bg-white shadow p-4 flex justify-between">
                <h1 className="text-xl font-bold">Raspberry Pi Platform</h1>
                <button onClick={() => { localStorage.removeItem('token'); window.location.href = '/login'; }}>Logout</button>
            </nav>

            <main className="container mx-auto p-6">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-semibold">Your Sites</h2>
                    <button
                        className="bg-green-600 text-white px-4 py-2 rounded"
                        onClick={() => setShowModal(true)}
                    >
                        + New Site
                    </button>
                </div>

                {loading ? <p>Loading...</p> : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {sites.map(site => (
                            <div key={site.id} className="bg-white p-6 rounded shadow">
                                <h3 className="text-lg font-bold">{site.display_name || site.slug}</h3>
                                <p className="text-sm text-gray-500">{site.domain || `${site.slug}.lan`}</p>
                                <div className="mt-2">
                                    <span className={`px-2 py-1 text-xs rounded ${site.status === 'deployed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                                        {site.status}
                                    </span>
                                </div>
                                <div className="mt-4">
                                    <label className="block text-sm text-gray-700">Deploy Content (.zip)</label>
                                    <input
                                        type="file"
                                        accept=".zip"
                                        className="mt-1 block w-full text-sm"
                                        onChange={(e) => {
                                            if (e.target.files[0]) handleUpload(site.slug, e.target.files[0]);
                                        }}
                                    />
                                </div>
                                <div className="mt-4 text-right">
                                    <a href={`http://${site.domain || site.slug + '.lan'}`} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                                        Visit Site &rarr;
                                    </a>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Simple Modal */}
                {showModal && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                        <div className="bg-white p-6 rounded shadow-lg w-96">
                            <h3 className="text-xl font-bold mb-4">Create New Site</h3>
                            <form onSubmit={handleCreateSite}>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium">Slug (URL path)</label>
                                    <input className="w-full border p-2 rounded" value={slug} onChange={e => setSlug(e.target.value)} required />
                                </div>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium">Display Name</label>
                                    <input className="w-full border p-2 rounded" value={displayName} onChange={e => setDisplayName(e.target.value)} />
                                </div>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium">Custom Domain (Optional)</label>
                                    <input className="w-full border p-2 rounded" value={domain} onChange={e => setDomain(e.target.value)} placeholder="example.com" />
                                </div>
                                <div className="flex justify-end gap-2">
                                    <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-gray-600">Cancel</button>
                                    <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">Create</button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

            </main>
        </div>
    );
}
