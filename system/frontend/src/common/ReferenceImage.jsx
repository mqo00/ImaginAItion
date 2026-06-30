import { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import sio from './websocket';
import { MetroSpinner } from 'react-spinners-kit';
import { getImageUrl } from '../config/api';

export default function ReferenceImage() {
  const { gameCode } = useParams();
  const [referenceImage, setReferenceImage] = useState(null);
  const [isLoadingReference, setIsLoadingReference] = useState(true);

  // get the reference image
  useEffect(() => {
    const fetchReferenceImage = async () => {
      if (!sio.id || !sio.connected) {
        setTimeout(fetchReferenceImage, 200);
        return;
      }
      
      try {
        setIsLoadingReference(true);
        const response = await axios.get(`/api/reference-image?room_id=${gameCode}&sid=${sio.id}`);
        setReferenceImage(response.data);
      } catch (error) {
        console.error('Error fetching reference image:', error);
      } finally {
        setIsLoadingReference(false);
      }
    };
    
    fetchReferenceImage();
  }, [gameCode]);

  return (
    <div className="bg-white rounded-lg border-2 border-black p-4 shadow-lg">
      {isLoadingReference ? (
        <div className="flex flex-col items-center py-4">
          <MetroSpinner loading={true} color="#111111" size={30} />
          <p className="mt-2 text-gray-600 text-sm">Loading...</p>
        </div>
      ) : referenceImage ? (
        <div className="text-center">
          <img
            src={getImageUrl(referenceImage.image_path)}
            alt={referenceImage.description}
            className="w-full h-72 rounded-lg object-contain mb-3"
            onError={(e) => {
              console.error('Failed to load image:', e.target.src);
              e.target.style.display = 'none';
            }}
          />
          <p className="text-sm font-medium text-gray-800">{referenceImage.description}</p>
        </div>
      ) : (
        <p className="text-gray-500 text-sm text-center py-4">No reference image</p>
      )}
    </div>
  );
}