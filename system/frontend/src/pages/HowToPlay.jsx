import '../App.css';
import TopBar from '../common/TopBar';
import Container from '../common/Container';
import BackButton from '../common/BackButton';

export default function HowToPlay() {
  return (
    <div className="h-svh flex flex-col">
      <div className="-z-10">
        <TopBar />
      </div>
      <div className="h-full items-center flex">
        <div className="main-container font-inter w-full text-[1rem]">
          <Container>
            <BackButton />
            <div className="grid grid-cols-3 justify-items-center pb-12 pl-20 pr-20 gap-x-6">
              <div className="col-start-1 col-span-full font-medium text-[2.5rem] mb-1 font-gooper">
                How to Play
              </div>
              <p1 className="block font-medium text-[1.25rem] col-start-1 col-span-full mb-[0.5rem] justify-self-start font-gooper">
                tl;dr
              </p1>
              <p1 className="block mb-[2rem] text-[#4E4E4E] col-start-1 col-span-full">
                Compete with your peers to see who can reproduce an image with generative AI most effectively!
                You want to make your generated image as similar as possible to the original one, but make your
                prompt as short as possible. Can AI do the right thing when you're so brief? The one who knows AI
                the best will win!
              </p1>
              <p1 className="block font-medium text-[1.25rem] col-start-1 col-span-full mb-[0.5rem] justify-self-start font-gooper">
                How it works
              </p1>
              <p1 className="block mb-[2rem] text-[#4E4E4E] col-start-1 col-span-full justify-self-start">
                This game needs at least{' '}
                <rem className="text-[#5A5A5A] font-bold">three players</rem> (for three teams) and has a total of{' '}
                <rem className="text-[#5A5A5A] font-bold">three steps</rem> in one round.
              </p1>
              <div className="bg-[#D7E5FF] rounded-[0.5rem] grid gap-3 p-8 mb-8 border-[0.125rem] border-black">
                <svg
                  width="32"
                  height="32"
                  viewBox="0 0 32 32"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M8.36085 0.370606C9.27536 0.125563 10.2154 0.668276 10.4604 1.58279L11.485 5.40648C11.73 6.32099 11.1873 7.26099 10.2728 7.50605C9.35826 7.75107 8.41826 7.20835 8.17321 6.29386L7.14866 2.47016C6.90361 1.55565 7.44633 0.61565 8.36085 0.370606ZM0.163727 8.58195C-0.0813158 9.49647 0.461398 10.4365 1.37591 10.6815L5.19959 11.7061C6.11411 11.9511 7.0541 11.4084 7.29916 10.4939C7.54421 9.57937 7.00149 8.63937 6.08697 8.39432L2.26329 7.36977C1.34878 7.12472 0.408771 7.66744 0.163727 8.58195ZM10.2201 13.0736C9.6238 11.2863 11.3244 9.58568 13.1117 10.182L29.3838 15.6108C31.4866 16.3124 31.4601 19.2961 29.3449 19.9599L24.712 21.4139L30.8834 27.5853C31.776 28.4779 31.776 29.925 30.8834 30.8178C29.9908 31.7104 28.5435 31.7104 27.651 30.8178L21.4651 24.632L19.998 29.3067C19.3342 31.4219 16.3505 31.4487 15.6489 29.3458L10.2201 13.0736ZM4.72375 20.0113C4.05429 20.6807 2.96885 20.6807 2.29938 20.0113C1.62991 19.3418 1.62991 18.2564 2.29938 17.5869L5.09852 14.7878C5.76798 14.1183 6.85342 14.1183 7.52288 14.7878C8.19235 15.4572 8.19235 16.5427 7.52288 17.2121L4.72375 20.0113ZM19.4896 4.94541C20.1591 4.27594 20.1591 3.19053 19.4896 2.52104C18.8202 1.85158 17.7348 1.85158 17.0653 2.52104L14.2662 5.32017C13.5967 5.98966 13.5967 7.07507 14.2662 7.74454C14.9356 8.41402 16.0211 8.41402 16.6905 7.74454L19.4896 4.94541Z"
                    fill="#111111"
                  />
                </svg>
                <p1 className="block font-medium font-gooper">Prompt</p1>
                <p1 className="block text-[#5A5A5A]">
                  Given an image, generate a reproduction of that image as close as
                  possible using your prompt, but use as <em>few</em> as possible words!
                </p1>
              </div>
              <div className="bg-[#D7E5FF] rounded-[0.5rem] grid gap-3 p-8 mb-8 border-[0.125rem] border-black">
                <svg
                  width="32"
                  height="32"
                  viewBox="0 0 32 32"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M9.94196 1.31919C12.6328 0.15312 15.5924 -0.250967 18.4973 0.151075C21.4023 0.553117 24.1408 1.74583 26.4139 3.59888C28.6864 5.45166 30.4064 7.8933 31.3854 10.6571C32.0011 12.3891 31.7273 14.3727 30.6654 15.873C29.6037 17.3728 27.8247 18.2903 25.987 18.2857H21.7111C20.895 18.2835 20.1048 18.5724 19.4826 19.1007C18.8605 19.6289 18.4472 20.3618 18.317 21.1675C18.1868 21.9732 18.3484 22.799 18.7726 23.4962C19.1968 24.1936 19.8558 24.7166 20.6312 24.9714C20.645 24.976 20.6588 24.9808 20.6724 24.9858C21.9297 25.453 22.8092 26.5902 22.8937 27.9246C23.0782 29.4576 22.078 30.989 20.5847 31.4085C19.1895 31.8048 17.7457 32.0039 16.2953 32C13.3632 31.9984 10.4878 31.1911 7.98327 29.6663C2.92384 26.5858 -0.0664058 20.8064 0.341911 14.8971C0.750226 8.98777 4.50695 3.67445 9.94196 1.31919ZM10.2857 16C12.1793 16 13.7143 14.465 13.7143 12.5714C13.7143 10.6779 12.1793 9.14286 10.2857 9.14286C8.39216 9.14286 6.85714 10.6779 6.85714 12.5714C6.85714 14.465 8.39216 16 10.2857 16ZM23.9998 9.14398C23.9998 11.0375 22.4647 12.5725 20.5712 12.5725C18.6776 12.5725 17.1426 11.0375 17.1426 9.14398C17.1426 7.25042 18.6776 5.71541 20.5712 5.71541C22.4647 5.71541 23.9998 7.25042 23.9998 9.14398ZM10.2854 23.9989C11.5478 23.9989 12.5712 22.9755 12.5712 21.7132C12.5712 20.4508 11.5478 19.4275 10.2854 19.4275C9.02306 19.4275 7.99972 20.4508 7.99972 21.7132C7.99972 22.9755 9.02306 23.9989 10.2854 23.9989Z"
                    fill="#111111"
                  />
                </svg>
                <p1 className="block font-medium font-gooper">Vote</p1>
                <p1 className="block text-[#5A5A5A]">
                  Now you get to be the judge! Among the images generated other
                  players, vote on the image most similar to the original image.
                </p1>
              </div>
              <div className="bg-[#D7E5FF] rounded-[0.5rem] grid gap-3 p-8 mb-8 border-[0.125rem] border-black">
                <svg
                  width="33"
                  height="32"
                  viewBox="0 0 33 32"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M23.1118 0C23.9187 0 24.5728 0.639593 24.5728 1.42857V3.30421C24.5728 4.09319 23.9187 4.73278 23.1118 4.73278C22.3049 4.73278 21.6508 4.09319 21.6508 3.30421V1.42857C21.6508 0.639593 22.3049 0 23.1118 0ZM9.46218 19.9729C12.5976 19.9729 15.1393 17.4876 15.1393 14.4219C15.1393 11.3562 12.5976 8.87088 9.46218 8.87088C6.32677 8.87088 3.785 11.3562 3.785 14.4219C3.785 17.4876 6.32677 19.9729 9.46218 19.9729ZM0 31.0747C0 25.9653 4.23626 21.8232 9.46195 21.8232C14.6876 21.8232 18.9239 25.9653 18.9239 31.0747C18.9239 31.5858 18.5003 32 17.9777 32H0.946195C0.423626 32 0 31.5858 0 31.0747ZM32.0645 5.69769C32.7249 5.24439 32.8846 4.35342 32.421 3.70766C31.9573 3.06192 31.046 2.90592 30.3856 3.35922L28.8157 4.43687C28.1553 4.89019 27.9956 5.78117 28.4592 6.4269C28.923 7.07266 29.8342 7.22866 30.4946 6.77536L32.0645 5.69769ZM13.7981 3.70766C13.3345 4.35342 13.4941 5.24439 14.1545 5.69769L15.7245 6.77536C16.3849 7.22866 17.2962 7.07266 17.7598 6.4269C18.2234 5.78117 18.0638 4.89019 17.4034 4.43687L15.8334 3.35922C15.1729 2.90592 14.2617 3.06192 13.7981 3.70766ZM23.0038 6.49182C25.8866 6.43328 28.3269 8.77915 28.3161 11.5984C28.2925 13.47 27.1452 15.2569 25.4314 16.091V18.6354C25.4277 18.7832 25.3648 18.9237 25.2563 19.027C25.1481 19.1301 25.0027 19.1879 24.8515 19.1878H21.3721C21.2208 19.1879 21.0755 19.1301 20.9672 19.027C20.8588 18.9237 20.7961 18.7832 20.7922 18.6354V16.1346C19.1308 15.3258 17.9969 13.6226 17.9129 11.8097C17.7823 8.9933 20.121 6.55035 23.0038 6.49182Z"
                    fill="#111111"
                  />
                </svg>
                <p1 className="block font-medium font-gooper">Reveal</p1>
                <p1 className="block text-[#5A5A5A]">
                  Check out all the prompts, images, votes, and the scores. Reflect
                  and learn from each other -- do better the next round!
                </p1>
              </div>
              <p1 className="block font-medium text-[1.25rem] col-start-1 col-span-full mb-[0.5rem] justify-self-start font-gooper">
                Scoring
              </p1>
              <p1 className="block text-[#4E4E4E] col-start-1 col-span-full justify-self-start">
                Players get one point for each vote from other players, and the one with the longest prompt gets one
                point penalty.
              </p1>
            </div>
          </Container>
        </div>
      </div>
    </div>
  );
}
