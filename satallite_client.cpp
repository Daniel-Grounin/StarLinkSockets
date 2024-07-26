#include <iostream>
#include <string>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <json/json.h>
#include <vector>

#pragma comment(lib, "Ws2_32.lib")

struct SatelliteData {
    double latitude;
    double longitude;
    double altitude;
};

void initializeWinsock() {
    WSADATA wsaData;
    int result = WSAStartup(MAKEWORD(2, 2), &wsaData);
    if (result != 0) {
        std::cerr << "WSAStartup failed: " << result << std::endl;
        exit(1);
    }
}

void cleanupWinsock() {
    WSACleanup();
}

std::string receiveData(SOCKET ConnectSocket) {
    char recvbuf[512];
    std::string data;
    int recvbuflen = 512;
    int recvResult;

    do {
        recvResult = recv(ConnectSocket, recvbuf, recvbuflen, 0);
        if (recvResult > 0) {
            data.append(recvbuf, recvResult);
        }
        else if (recvResult == 0) {
            std::cout << "Connection closed" << std::endl;
        }
        else {
            std::cerr << "recv failed: " << WSAGetLastError() << std::endl;
            closesocket(ConnectSocket);
            return "";
        }
    } while (recvResult == recvbuflen);  // Continue reading until the buffer is not full

    return data;
}

int main() {
    initializeWinsock();

    std::string server_ip = "127.0.0.1";
    int port = 65432;
    struct addrinfo* result = NULL, * ptr = NULL, hints;
    ZeroMemory(&hints, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_protocol = IPPROTO_TCP;

    std::string port_str = std::to_string(port);
    int result_int = getaddrinfo(server_ip.c_str(), port_str.c_str(), &hints, &result);
    if (result_int != 0) {
        std::cerr << "getaddrinfo failed: " << result_int << std::endl;
        WSACleanup();
        return 1;
    }

    SOCKET ConnectSocket = socket(result->ai_family, result->ai_socktype, result->ai_protocol);
    if (ConnectSocket == INVALID_SOCKET) {
        std::cerr << "Error at socket(): " << WSAGetLastError() << std::endl;
        freeaddrinfo(result);
        WSACleanup();
        return 1;
    }

    result_int = connect(ConnectSocket, result->ai_addr, (int)result->ai_addrlen);
    if (result_int == SOCKET_ERROR) {
        closesocket(ConnectSocket);
        ConnectSocket = INVALID_SOCKET;
    }

    freeaddrinfo(result);

    if (ConnectSocket == INVALID_SOCKET) {
        std::cerr << "Unable to connect to server!" << std::endl;
        WSACleanup();
        return 1;
    }

    std::cout << "Connected to the server at " << server_ip << ":" << port << std::endl;

    while (true) {
        std::string response = receiveData(ConnectSocket);

        if (!response.empty()) {
            Json::CharReaderBuilder readerBuilder;
            Json::Value root;
            std::string errs;
            std::istringstream s(response);
            bool parsingSuccessful = Json::parseFromStream(readerBuilder, s, &root, &errs);
            if (!parsingSuccessful) {
                std::cerr << "Failed to parse the response: " << errs << std::endl;
            }
            else {
                try {
                    for (const auto& sat : root) {
                        if (sat.isMember("name") && sat.isMember("latitude") && sat.isMember("longitude") && sat.isMember("altitude")) {
                            std::string name = sat["name"].asString();
                            double latitude = sat["latitude"].asDouble();
                            double longitude = sat["longitude"].asDouble();
                            double altitude = sat["altitude"].asDouble();

                            std::cout << "Satellite: " << name << std::endl;
                            std::cout << "Latitude: " << latitude << std::endl;
                            std::cout << "Longitude: " << longitude << std::endl;
                            std::cout << "Altitude: " << altitude << std::endl;
                            std::cout << std::endl;
                        }
                    }
                }
                catch (const std::exception& ex) {
                    std::cerr << "Exception occurred: " << ex.what() << std::endl;
                }
            }
        }

        Sleep(10000); // Wait for 10 seconds before the next request
    }

    closesocket(ConnectSocket);
    cleanupWinsock();
    return 0;
}
