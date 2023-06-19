import axios from 'axios';
import fs from 'fs'


async function fetchAzureVMSizes() {
  try {
    const url = 'https://azure.microsoft.com/api/v2/pricing/virtual-machines-base/calculator/';
    const region = 'us-east-2'
    const response = await axios.get(url);
    const vmSizes = response.data.offers;
    const final = []
    // Process and display the VM sizes
    Object.keys(vmSizes).forEach(offerKey => {

      const offer = vmSizes[offerKey];
      if(offer.prices[region]){
        final.push({
          "InstanceType" : offerKey,
          "CPU" : offer.cores,
          "Memory" : offer.ram,
          "Storage" : offer.diskSize,
          "Cost" : offer.prices[region].value,
        })
      }
      // console.log(`VM Size: ${offerKey}`);
    });
    const jsonContent = JSON.stringify(final, null, 2);

    fs.writeFile('azure.json', jsonContent, (error) => {
      if (error) {
        console.error('Error writing to JSON file:', error);
      } else {
        console.log('Data saved to azureData.json');
      }
    });
  } catch (error) {
    console.error('Error fetching Azure VM sizes:', error.message);
  }
}

// Call the function to fetch Azure VM sizes
fetchAzureVMSizes();
