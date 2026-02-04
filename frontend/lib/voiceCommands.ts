import { Property } from '@/store/useAgentStore'

/**
 * Voice command processor for AI agent
 * This simulates how an AI would interpret voice commands and trigger UI actions
 */

export interface VoiceCommandResult {
  success: boolean
  message: string
  action?: 'show_property' | 'list_properties' | 'filter_properties' | 'unknown'
  data?: any
}

export class VoiceCommandProcessor {
  private properties: Property[]

  constructor(properties: Property[]) {
    this.properties = properties
  }

  /**
   * Process natural language command about properties
   * Examples:
   * - "Show me the property on Broadway"
   * - "Tell me about 123 Main Street"
   * - "What properties do we have on Park Avenue"
   * - "Show me details for the Downtown Loft"
   */
  processCommand(command: string): VoiceCommandResult {
    const lowerCommand = command.toLowerCase()

    // Pattern: "show me" + address/description
    if (lowerCommand.includes('show me') || lowerCommand.includes('tell me about')) {
      return this.findAndShowProperty(command)
    }

    // Pattern: "details for" + address
    if (lowerCommand.includes('details for') || lowerCommand.includes('detail view')) {
      return this.findAndShowProperty(command)
    }

    // Pattern: asking about specific address
    if (lowerCommand.includes('broadway') ||
        lowerCommand.includes('main') ||
        lowerCommand.includes('park avenue') ||
        /\d+/.test(command)) { // Contains numbers (likely an address)
      return this.findAndShowProperty(command)
    }

    return {
      success: false,
      message: "I didn't understand that command",
      action: 'unknown'
    }
  }

  private findAndShowProperty(command: string): VoiceCommandResult {
    const lowerCommand = command.toLowerCase()

    // Try to find property by address parts
    let foundProperty: Property | undefined

    // Search by street name
    const streetKeywords = ['broadway', 'main', 'park avenue', 'avenue', 'street', 'st', 'ave']
    for (const keyword of streetKeywords) {
      if (lowerCommand.includes(keyword)) {
        foundProperty = this.properties.find(p =>
          p.address.toLowerCase().includes(keyword)
        )
        if (foundProperty) break
      }
    }

    // Search by street number
    if (!foundProperty) {
      const numberMatch = command.match(/\d+/)
      if (numberMatch) {
        const number = numberMatch[0]
        foundProperty = this.properties.find(p =>
          p.address.includes(number)
        )
      }
    }

    // Search by property type or description
    if (!foundProperty) {
      const typeKeywords = ['condo', 'loft', 'house', 'apartment', 'townhouse']
      for (const keyword of typeKeywords) {
        if (lowerCommand.includes(keyword)) {
          foundProperty = this.properties.find(p =>
            p.title?.toLowerCase().includes(keyword) ||
            p.property_type?.toLowerCase().includes(keyword)
          )
          if (foundProperty) break
        }
      }
    }

    if (foundProperty) {
      return {
        success: true,
        message: `Found ${foundProperty.address}`,
        action: 'show_property',
        data: foundProperty
      }
    }

    return {
      success: false,
      message: "I couldn't find that property. Can you be more specific?",
      action: 'show_property'
    }
  }

  /**
   * Find property by exact or partial address match
   */
  findPropertyByAddress(address: string): Property | null {
    const lowerAddress = address.toLowerCase()

    // Try exact match first
    let property = this.properties.find(p =>
      p.address.toLowerCase() === lowerAddress
    )

    // Try partial match
    if (!property) {
      property = this.properties.find(p =>
        p.address.toLowerCase().includes(lowerAddress) ||
        lowerAddress.includes(p.address.toLowerCase())
      )
    }

    return property || null
  }
}

/**
 * Example usage for AI integration:
 *
 * const processor = new VoiceCommandProcessor(properties)
 * const result = processor.processCommand("Show me the property on Broadway")
 *
 * if (result.success && result.action === 'show_property') {
 *   setFocusedProperty(result.data)
 *   setCurrentMessage(result.message)
 * }
 */
