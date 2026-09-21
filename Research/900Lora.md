# LoRa Research

## What is LoRa
LoRa, meaning "Long Range," is a low-power wireless radio technology designed to transmit small amounts of data over long distances. 
LoRa uses Chirp Spread Spectrum (CSS). A chirp is a signal whose frequency increases from low to high or decreases from high to low over time. 
Bandwidth describes the range of frequencies occupied by the LoRa signal. A wider bandwidth generally allows a higher data rate and shorter transmission time, but it can reduce receiver sensitivity and communication range. A narrower bandwidth generally provides better sensitivity and range, but results in a lower data rate. 
LoRa performance also depends on the spreading factor. A higher spreading factor improves sensitivity and range but increases transmission time. A lower spreading factor provides a higher data rate but usually reduces range. 
[Watch this chirp explanation](https://www.youtube.com/watch?v=dxYY097QNs0)

### URC Sub-Band Configuration
According to Section 3.b.v of the 2026 University Rover Challenge rules, our 900 MHz communication system has to be able to operate within these three sub-bands: 
-**900-Low:** (902 - 910 MHz)
-**900-Mid:** (911 - 919 MHz)
-**900-High:** (920 - 928 MHz)

The competition schedule will tell teams which sub-bands they may use during each mission. So our system has to be able to change the frequency or channel to fit inside the sub-band. 

The system does not use all three sub-band simultaneously. It operates within whichever sub-band URC assigns for that mission.

## Sub-Band Differences

The three sub-bands basically operate the same way besides the main differences: 
- Frequencies and channels available within each sub-band
- The amount of interference present from nearby devices or teams
- Small differences in antenna performance across the frequency range 

### Constraints
- No frequency bandwidths greater than 8Mhz 
- All 900 MHz transmissions must remain inside the sub-band assigned for the mission. 
- The team must be able to switch between all three designated sub-bands. 
- The team should expect other teams to operate nearby on different 900 MHz sub-bands. 

## LoRa Module Interfaces 

UART and SPI are two of the most popular interfaces that can be used to connect a microcontroller to a LoRa radio module. 

### SPI 
SPI modules typically give the microcontroller more direct control over the LoRa transceiver. 

#### Advantages
- Provides faster communication between the STM32 and radio.
- Gives the programmer more control over radio settings and packet handling.
- Multiple devices can share the same SPI bus
- Has advanced radio features. 

#### Disadvantages 
- Requires more signal connections, including clock, data, chip-select, and usually interrupt, reset, and busy signals. 
- Requiresm more complicated firmware and configuration.
- The STM32 must manage more of the radio state, interrupts, packets, and errors. 
- Harder to debug. 

### UART
UART LoRa modules usually contain an additional controller that manages the radio. The STM32 communicates with that controller using serial commands, called AT commands. 

#### Advantages
- Easier to configure and program.
- Usually requires only transmit and receive connections
- AT commands can configure the frequency, address, and bandwidth
- Commands and responses can be tested using a serial terminal 

### Disadvantages 
- Usually provides less direct control over the LoRa transceiver. 
- Available features depend on the commands provided by the module manufacturer. 
- UART is normally a point-to-point connection between one microcontroller and one module. 
- Incoming bytes can be lost if the STM32 does not empty the receive buffer quickly. 
