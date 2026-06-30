import TopBar from '../common/TopBar';
import Container from '../common/Container';
import axios from 'axios';
import { useState } from 'react';

export default function Image() {
  const [img, setImg] = useState(null);
  const [imageName, setImageName] = useState(''); // Store input value

  const getImage = async () => {
    if (!imageName.trim()) {
      alert('Please enter an image name!');
      return;
    }

    try {
      const response = await axios.get(`/api/image?image_name=${imageName}`, {
        responseType: 'blob',
      });

      const imageUrl = URL.createObjectURL(response.data);
      setImg(imageUrl);

      return () => URL.revokeObjectURL(imageUrl); // Cleanup URL
    } catch (error) {
      console.error('Error fetching image:', error);
      alert('Failed to load image. Check console.');
    }
  };
  return (
    <div className="h-svh flex flex-col">
      <div className="-z-10">
        <TopBar />
      </div>
      <div className="h-full items-center flex">
        <div className="main-container font-inter w-full">
          <Container>
            <div className="p-[2rem] justify-items-center">
              <div className="w-full">
                <form className="flex p-2 w-full">
                  <input
                    type="text"
                    value={imageName}
                    onChange={(e) => setImageName(e.target.value)}
                    className="bg-transparent w-full focus:outline-none border-b-2 border-black text-[1.5rem]"
                    placeholder="Enter image name (e.g. img-Zk1NQMQhLCkhzIyjIyFycUQX.png)"
                  />
                </form>
                <button
                  onClick={getImage}
                  className="w-full font-medium border border-black rounded-xl text-[1.5rem] text-[#FFFFFF] pl-8 pr-8 pb-3 pt-3 bg-[#111111] col-start-2 col-span-2 justify-self-center font-gooper"
                >
                  Load image
                </button>
              </div>
              {img && (
                <div>
                  <img src={img} alt="image" className="mt-[2rem]" />
                  <button
                    onClick={() => {
                      if (!img) {
                        alert('No image to download!');
                        return;
                      }
                      const link = document.createElement('a');
                      link.href = img;
                      link.download = imageName || 'downloaded_image'; // Set the filename
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                    }}
                    className="font-medium border border-black rounded-xl text-[1.5rem] mt-[1rem] text-[#FFFFFF] pl-8 pr-8 pb-3 pt-3 bg-[#111111] col-start-2 col-span-2 justify-self-center font-gooper"
                  >
                    Download image
                  </button>
                </div>
              )}
            </div>
          </Container>
        </div>
      </div>
    </div>
  );
}
