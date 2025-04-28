# BUtLAR: Voice-Powered Digital Human Assistant
# Engineering Addendum for Future Groups

**Introduction:**
----------------------------------------------------------------------------------------------------

Meet BUtLAR! BUtLAR is an innovative audio responder capable of natural, voice-based conversations, offering users a more personalized and accurate experience across diverse categories. The responder is voice-activated and aims to highlight the advanced audio processing that Yobe, our client, offers. BUtLAR has capabilities to seamlessly integrate features from Yobe Inc. that personalize audio processing through speaker identification, noise immunity, and answer generation in real-time. The overall design of BUtLAR emphasizes natural conversation and provides accurate responses to user queries. These components offer a cohesive product that highlights the powerful features of Yobe’s product.

Our current implementation does not include Yobe's SDK. The SDK release we had access to was far more compatible with a one-query model, which we previously implemented. We wanted to emphasize the conversational aspect of BUtLAR, and therefore do not utilize the previous SDK. However, Yobe's new SDK has extensive potential for integrating a real-time audio capture. This repository serves as the groundwork for implementing the new SDK, called BioPSI.

Our design integrates Yobe’s Audio Processing SDK, OpenAI’s LLM, Google ASR, and a streamlined, minimalistic hardware setup to bring all components together. When a user asks a question, BUtLAR will retrieve a query from audio processed by Yobe’s SDK (“listen”), process the data with LLMs to formulate a correct response (“think”), and then relay this information to the user (“speak”). 

**Important Things to Know:**
----------------------------------------------------------------------------------------------------
While working with real-time streaming with the Yobe SDK, please keep the following in mind:
* It is important to understand how splitting buffers would affect subsequent steps in our pipeline (i.e., if a word gets split, how the ASR would process this)
* Please keep in mind the Yobe SDK uses 4096-sized buffers; subsequent processing must match this size to ensure compatibility.
For other components of our pipeline, please keep the following in mind:
* Our framework is intended to be context-dependent. This means that you may replace our database with a database of your choice to enable BUtLAR to curate answers pertinent to the content of your choice. Essentially, future groups should modify the database to their use-case-specific scenario. Our current database pertains to Spring 2025 courses at Boston University.
* Please update the Google ASR account and OpenAI API key. We have terminated our temporary Google Cloud account. We stored confidential keys in our .env folder.
* We ran into issues where the responder was stuck in a feedback loop — that is, the responder would capture its own Text-To-Speech (TTS) output as input, thinking it was a query from the user. To address this, we had to employ audio flushing based on the length of the TTS output. This is important to keep in mind when understanding the audio capture processes, especially when supporting looping conversations. It’s also worthwhile to note that this sometimes triggered an error in the Google ASR capture, specifically an Error 400 message. The ASR expects constant audio streaming, so flushing the audio disrupted this. Our system also uses a flag-based mechanism to manage conversation flow, pausing audio capture during system responses. 
* We encountered challenges with the Raspberry Pi's local file handling for audio output (text-to-speech). To address this limitation, we implemented a Web Speech API text-to-speech (TTS) solution instead of continuing with OpenAI's TTS, which had been saving each response as an MP3 file. This approach created issues where each new response would overwrite the previous file and remain inaccessible for playback from the Pi. If future groups want to change this API, this is an important consideration to keep in mind. 


**Future Advancements:**
----------------------------------------------------------------------------------------------------
The main advancement our product would benefit from involves integrating the new BioPSI Yobe SDK. To fully complete the product, future teams should focus on implementing the templating stage for the new SDK and configuring it to support both denoising and biometric tracking capabilities. The foundation we've established this semester provides a foundation for these features, which will further improve BUtLAR's ability to function in noisy environments and personalize responses based on speaker identification. With this new SDK, groups can reconsider the need for a Raspberry-Pi. BioPSI is mac-based so keeping the implementation local is another approach to perhaps test.

Our ASR processing does not transcribe with high accuracy. Future groups can consider other providers (other than Google) to boost this.

There is also room for improvement in the user interface. While we envisioned a more futuristic design with a pulsing circle animation, groups should use creative freedom to design what they think displays BUtLAR the best. 

Finally, although our database and retrieval system have become more robust, future groups can aim to further improve search accuracy by integrating VannaAI. This will help address inconsistencies we encountered—for example, when a query occasionally produced an incorrect response but succeeded upon being repeated.


**How to Use:**
----------------------------------------------------------------------------------------------------
Establish SSH connectivity to the Raspberry Pi for remote access using the command:
ssh yobe@128.197.180.176

Navigate to the appropriate directory:
cd BUtLAR_Voice-Powered-Digital_Human_Assistant/Audio/testing_audio/django_top
```bash
Running the Session
1. Activate the GCloud virtual environment:
<br/>source ~/gcloudenv/bin/activate
2. Start the server:
<br/>daphne -b 127.0.0.1 -p 8000 django_top.asgi:application
3. Access the BUtLAR interface by navigating to:
<br/>http://127.0.0.1:8000/butlar/interface/
4. Press Enter to begin the session.
```

## Contributors

**Noa Margolin¹**, **Suhani Mitra²**, **Jackie Salamy³**, **Andrew Sasamori⁴**

¹ [Department of Electrical and Computer Engineering](https://www.bu.edu/eng/departments/ece/), Boston University, Boston, MA, 02215  
Email: [noam@bu.edu](mailto:noam@bu.edu)

² [Department of Electrical and Computer Engineering](https://www.bu.edu/eng/departments/ece/), [Department of Computer Science](https://www.bu.edu/cs/), [Department of Mathematics and Statistics](https://www.bu.edu/math/) Boston University, Boston, MA, 02215  
Email: [suhanim@bu.edu](mailto:suhanim@bu.edu)

³ [Department of Electrical and Computer Engineering](https://www.bu.edu/eng/departments/ece/), Boston University, Boston, MA, 02215  
Email: [jesalamy@bu.edu](mailto:jesalamy@bu.edu)

⁴ [Department of Electrical and Computer Engineering](https://www.bu.edu/eng/departments/ece/), Boston University, Boston, MA, 02215  
Email: [sasamori@bu.edu](mailto:sasamori@bu.edu)

----------------------------------------------------------------------------------------------------

[**Yobe**](https://yobeinc.com/), 77 Franklin St, Boston, MA 02110  
Phone: (617) 848 8922  
Email: [contact.us@yobeinc.com](mailto:contact.us@yobeinc.com)

## Internal Links:
[Shared Drive](https://drive.google.com/drive/u/1/folders/0APRJN7ri7rJUUk9PVA)
