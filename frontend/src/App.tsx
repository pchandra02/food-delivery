import { ChakraProvider, Box, Heading, Container } from '@chakra-ui/react';
import ChatInterface from './components/ChatInterface';

function App() {
  return (
    <ChakraProvider>
      <Box minH="100vh" bg="gray.50">
        <Container maxW="container.xl" py={4}>
          <Heading as="h1" size="xl" textAlign="center" mb={8}>
            Food Delivery Support Chat
          </Heading>
          <ChatInterface />
        </Container>
      </Box>
    </ChakraProvider>
  );
}

export default App;
