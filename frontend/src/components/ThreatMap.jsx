import { useMemo, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { severityColor, markerRadius } from '../utils';
import './ThreatMap.css';

function createThreatIcon(color, size) {
  const dim = size * 4;
  return L.divIcon({
    className: 'threat-marker-icon',
    html: `
      <div class="threat-marker" style="--m-color:${color};--m-size:${size}px">
        <span class="threat-marker-pulse"></span>
        <span class="threat-marker-glow"></span>
        <span class="threat-marker-core"></span>
      </div>
    `,
    iconSize: [dim, dim],
    iconAnchor: [dim / 2, dim / 2],
  });
}

function MapBounds({ markers }) {
  const map = useMap();
  useEffect(() => {
    if (!markers.length) return;
    const bounds = L.latLngBounds(
      markers.map((m) => [m.lat, m.lng])
    );
    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 6 });
  }, [markers, map]);
  return null;
}

function normalizeMarker(ioc) {
  const lat = Number(ioc.latitude);
  const lng = Number(ioc.longitude);
  if (Number.isNaN(lat) || Number.isNaN(lng)) return null;
  return { ...ioc, lat, lng };
}

export default function ThreatMap({ iocs = [] }) {
  const markers = useMemo(() => {
    return iocs
      .filter((ioc) => ioc.ioc_type === 'ip')
      .map(normalizeMarker)
      .filter(Boolean);
  }, [iocs]);

  const center = useMemo(() => {
    if (markers.length === 0) return [20, 0];
    const avgLat = markers.reduce((s, m) => s + m.lat, 0) / markers.length;
    const avgLon = markers.reduce((s, m) => s + m.lng, 0) / markers.length;
    return [avgLat, avgLon];
  }, [markers]);

  return (
    <div className="threat-map-panel">
      <h2 className="font-mono section-title">// THREAT MAP</h2>
      <div className="map-container">
        <div className="map-scanlines" aria-hidden="true" />
        <MapContainer
          center={center}
          zoom={2}
          className="leaflet-map"
          key={`map-${markers.length}`}
        >
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png"
          />
          <MapBounds markers={markers} />
          {markers.map((ioc) => {
            const color = severityColor(ioc.severity);
            const size = markerRadius(ioc.severity);
            return (
              <Marker
                key={ioc.id}
                position={[ioc.lat, ioc.lng]}
                icon={createThreatIcon(color, size)}
              >
                <Popup>
                  <div className="map-popup">
                    <strong>{ioc.value}</strong>
                    <p>Score: {ioc.threat_score.toFixed(1)} ({ioc.severity})</p>
                    <p>Country: {ioc.country || 'Unknown'}</p>
                    {ioc.tags?.length > 0 && (
                      <p>Tags: {ioc.tags.join(', ')}</p>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
      <p className="map-legend font-mono">
        {markers.length} IP IOCs plotted
      </p>
    </div>
  );
}
